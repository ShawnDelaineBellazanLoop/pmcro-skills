#!/usr/bin/env python3
"""Durable file-backed queue for PhaseMessages, and the drain that delivers them.

Why a queue at all: ingress arrives when it arrives, and a cycle may be mid-phase
or waiting on a human. A queue lets delivery be decided by the Orchestrator's
gates rather than by whoever happened to call first.

Durability here is directory state plus atomic rename, which is the smallest
mechanism that survives a crash on Windows and POSIX alike:

  pending/     accepted, not yet leased
  processing/  leased by a drain, with a visibility deadline
  done/        delivered (or recognized as a replay) and acknowledged
  held/        blocked on human approval - LAW-008, not a failure
  dead/        exhausted retries or refused by contract - needs a human

A crashed drain leaves a message in processing/ with an expired lease; the next
drain reclaims it. That makes delivery at-least-once, which is safe only because
the dispatcher suppresses replays by idempotency_key (ARCH-007).

This adapter is the reference implementation of the queue contract. Swapping in a
real broker means implementing enqueue/lease/ack/nack with the same semantics -
the gates stay in the dispatcher either way (ARCH-005).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import dispatch_message as dm  # noqa: E402
import pmcro_runtime as rt  # noqa: E402

STATES = ("pending", "processing", "done", "held", "dead")


def queue_root(root: pathlib.Path) -> pathlib.Path:
    path = root / rt.CONTROL_PLANE / "queue"
    for state in STATES:
        (path / state).mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write(path: pathlib.Path, payload: dict) -> pathlib.Path:
    """Write to a temp name and rename, so a reader never sees a half-written job."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)
    return path


def _job_name(message: dict) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in message["message_id"])
    return f"{int(time.time() * 1000):013d}-{safe}.json"


def enqueue(root: pathlib.Path, message: dict, *, origin: str = "local") -> dict:
    """Accept a message for later delivery. Contract is checked at the door.

    Refusing a malformed envelope here keeps the queue free of jobs that can only
    ever fail, but the envelope is checked again at dispatch, because a file on
    disk can be edited between enqueue and delivery.
    """
    errors = rt.validate_against(root, message, "phase-message.schema.json")
    if errors:
        return {"status": "refused", "errors": errors}
    job = {
        "job_id": _job_name(message).removesuffix(".json"),
        "origin": origin,
        "attempts": 0,
        "enqueued_utc": rt.utc_now(),
        "lease_expires": None,
        "message": message,
    }
    path = _atomic_write(queue_root(root) / "pending" / _job_name(message), job)
    return {"status": "queued", "job_id": job["job_id"], "path": str(path)}


def _limits(root: pathlib.Path) -> tuple[int, int]:
    config = rt.load_config(root)
    return int(config.get("queue_lease_seconds", 120)), int(config.get("max_queue_attempts", 3))


def lease(root: pathlib.Path, *, now: float | None = None) -> pathlib.Path | None:
    """Claim the oldest deliverable job, reclaiming any whose lease has expired.

    Reclaiming is what makes a crashed drain recoverable rather than a stuck
    queue; the cost is that a job can be delivered twice, which the dispatcher's
    idempotency ledger absorbs.
    """
    now = time.time() if now is None else now
    lease_seconds, _ = _limits(root)
    paths = queue_root(root)

    for stale in sorted((paths / "processing").glob("*.json")):
        job = rt.load_json(stale)
        if (job.get("lease_expires") or 0) <= now:
            os.replace(stale, paths / "pending" / stale.name)

    for candidate in sorted((paths / "pending").glob("*.json")):
        job = rt.load_json(candidate)
        job["lease_expires"] = now + lease_seconds
        job["attempts"] = job.get("attempts", 0) + 1
        target = paths / "processing" / candidate.name
        _atomic_write(target, job)
        candidate.unlink()
        return target
    return None


def _move(path: pathlib.Path, state: str, root: pathlib.Path, **fields) -> pathlib.Path:
    job = rt.load_json(path)
    job.update(fields)
    job["lease_expires"] = None
    job[f"{state}_utc"] = rt.utc_now()
    target = _atomic_write(queue_root(root) / state / path.name, job)
    path.unlink()
    return target


def ack(root: pathlib.Path, path: pathlib.Path, result: dict) -> pathlib.Path:
    return _move(path, "done", root, result=result)


def nack(root: pathlib.Path, path: pathlib.Path, reason: dict) -> pathlib.Path:
    """Return a job for retry, or retire it to the dead letter at the attempt limit.

    A dead letter is deliberately a terminal, visible state: silently retrying a
    message forever is how a bounded system becomes an unbounded one (LAW-007).
    """
    _, max_attempts = _limits(root)
    job = rt.load_json(path)
    if job.get("attempts", 0) >= max_attempts:
        return _move(path, "dead", root, reason=reason, verdict="ESCALATE")
    job["lease_expires"] = None
    job["last_error"] = reason
    target = _atomic_write(queue_root(root) / "pending" / path.name, job)
    path.unlink()
    return target


def hold(root: pathlib.Path, path: pathlib.Path, reason: dict) -> pathlib.Path:
    return _move(path, "held", root, reason=reason)


def drain(root: pathlib.Path, *, limit: int = 50, approved: bool = False) -> list[dict]:
    """Deliver queued messages through the dispatcher, one gate decision each.

    The drain never decides anything itself: it turns the dispatcher's exit code
    into a queue state, so queue behavior and cycle governance cannot drift apart.
    """
    outcomes: list[dict] = []
    for _ in range(limit):
        leased = lease(root)
        if leased is None:
            break
        job = rt.load_json(leased)
        code, result = dm.dispatch(root, job["message"], approved=approved)
        outcomes.append({"job_id": job["job_id"], "exit_code": code, **result})

        if code == dm.EXIT_OK:
            ack(root, leased, result)
        elif code == dm.EXIT_APPROVAL:
            hold(root, leased, result)
        elif code in (dm.EXIT_CONTRACT, dm.EXIT_ROUTING):
            _move(leased, "dead", root, reason=result, verdict="ESCALATE")
        else:
            nack(root, leased, result)
    return outcomes


def status(root: pathlib.Path) -> dict:
    paths = queue_root(root)
    return {state: len(list((paths / state).glob("*.json"))) for state in STATES}


def main() -> int:
    parser = argparse.ArgumentParser(description="PMCRO durable queue adapter.")
    parser.add_argument("command", choices=["enqueue", "drain", "status"])
    parser.add_argument("--message", help="PhaseMessage JSON file (enqueue)")
    parser.add_argument("--root", default=None)
    parser.add_argument("--origin", default="local")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--approved", action="store_true", help="authorize held messages during this drain")
    args = parser.parse_args()

    start = pathlib.Path(args.message) if args.message else pathlib.Path(__file__)
    root = pathlib.Path(args.root).resolve() if args.root else rt.find_root(start)

    if args.command == "enqueue":
        if not args.message:
            parser.error("--message is required for enqueue")
        result = enqueue(root, rt.load_json(args.message), origin=args.origin)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "queued" else 1

    if args.command == "drain":
        outcomes = drain(root, limit=args.limit, approved=args.approved)
        print(json.dumps({"drained": len(outcomes), "outcomes": outcomes}, indent=2))
        return 0 if all(o["exit_code"] == dm.EXIT_OK for o in outcomes) else 3

    print(json.dumps(status(root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
