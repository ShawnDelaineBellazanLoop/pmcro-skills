#!/usr/bin/env python3
"""Dispatch a typed PhaseMessage at the PMCRO Orchestrator boundary.

A PhaseMessage is what is sent; SendMessage, a queue, or a MAF host adapter are
transports that carry it (docs/phase-message-vs-send-message.md). Whatever the
transport, delivery has to pass the same gates, so those gates live here rather
than in each adapter:

  contract  - the envelope matches phase-message.schema.json
  routing   - the edge is forward-only (LAW-001)
  replay    - a repeated idempotency_key delivers once (at-least-once transports)
  bounds    - per-phase attempts stay under the configured limit (LAW-007)
  approval  - a message marked requires_approval waits for a human (LAW-008)

A delivered message leaves a hash-chained handoff TrailFrame and one append-only
trail event, so the route a cycle actually took can be reconstructed from
evidence instead of from an agent's account of it (LAW-002, LAW-010).

Exit codes: 0 delivered or duplicate, 1 contract violation, 2 routing violation,
3 attempt limit reached, 4 approval required.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pmcro_runtime as rt  # noqa: E402


# Forward-only edges. A phase never reaches back to an earlier phase: a failed
# check travels checker -> reflector -> orchestrator, and the Orchestrator opens
# a new cycle. Allowing checker -> maker would let two agents repair each other
# with no record and no bound, which is what LAW-001 exists to prevent.
ROUTES = {
    "system": {"planner"},
    "planner": {"maker"},
    "maker": {"checker"},
    "checker": {"reflector"},
    "reflector": {"orchestrator"},
    "orchestrator": {"planner", "system"},
}

EXIT_OK = 0
EXIT_CONTRACT = 1
EXIT_ROUTING = 2
EXIT_BOUNDS = 3
EXIT_APPROVAL = 4


def route_errors(message: dict, ledger: dict) -> list[str]:
    source = message["source"]
    target = message["target"]
    allowed = ROUTES.get(source)
    if allowed is None:
        return [f"unknown source phase '{source}'"]
    if target not in allowed:
        return [f"backward or undefined edge {source} -> {target}; allowed: {sorted(allowed)}"]
    if source == "orchestrator" and target == "planner":
        # Re-entering planning is opening a new cycle, and a new cycle needs its
        # own id or the attempt counters and the Trail both lose their meaning.
        if rt.cycle_entries(ledger, message["cycle_id"]):
            return [f"orchestrator -> planner must open a new cycle_id; '{message['cycle_id']}' already has dispatches"]
    return []


def dispatch(root: pathlib.Path, message: dict, approved: bool = False) -> tuple[int, dict]:
    """Run every gate in order and, if all pass, record the handoff.

    Returns (exit_code, result). The result is the operator-facing record of what
    happened, and is also what the caller prints, so a blocked dispatch explains
    itself instead of failing silently.
    """
    errors = rt.validate_against(root, message, "phase-message.schema.json")
    if errors:
        return EXIT_CONTRACT, {"status": "contract-violation", "errors": errors}

    ledger = rt.load_ledger(root)

    duplicate = rt.find_by_idempotency_key(ledger, message.get("idempotency_key", ""))
    if duplicate:
        return EXIT_OK, {
            "status": "duplicate",
            "message_id": duplicate["message_id"],
            "frame_ref": duplicate["frame_ref"],
            "note": "idempotency_key already delivered; no new frame or event written",
        }

    violations = route_errors(message, ledger)
    if violations:
        return EXIT_ROUTING, {"status": "routing-violation", "errors": violations}

    config = rt.load_config(root)
    limit = config.get("max_phase_attempts", 2)
    prior = rt.attempts_for(ledger, message["cycle_id"], message["target"])
    if prior >= limit:
        return EXIT_BOUNDS, {
            "status": "attempt-limit",
            "verdict": "ESCALATE",
            "target": message["target"],
            "attempts": prior,
            "limit": limit,
        }

    if message.get("requires_approval") and not approved:
        return EXIT_APPROVAL, {
            "status": "approval-required",
            "message_id": message["message_id"],
            "note": "re-run with --approved once a human has authorized this dispatch",
        }

    return EXIT_OK, _record(root, message, ledger, approved)


def _record(root: pathlib.Path, message: dict, ledger: dict, approved: bool) -> dict:
    """Write the handoff frame, the trail event, and the ledger entry."""
    sequence = len(ledger.get("dispatches", [])) + 1
    frame_id = f"frame-{message['cycle_id']}-dispatch-{sequence:03d}"
    payload_sha256 = rt.sha256_of(message)

    frame = {
        "type": "TrailFrame",
        "frame_id": frame_id,
        "cycle_id": message["cycle_id"],
        "phase": message["target"],
        "frame_type": "handoff",
        "summary": (
            f"Dispatched {message['message_type']} from {message['source']} to "
            f"{message['target']} (message {message['message_id']}"
            + (", human-approved" if approved else "")
            + ")."
        ),
        "evidence_refs": [r for r in (message.get("payload_ref"), message.get("frame_ref")) if r],
        "source_refs": [".pmcro/schemas/phase-message.schema.json"],
        "confidence": "high",
        "payload_sha256": payload_sha256,
        "previous_frame_hash": rt.last_frame_hash(ledger),
        "created_utc": rt.utc_now(),
    }

    frame_errors = rt.validate_against(root, frame, "trail-frame.schema.json")
    if frame_errors:  # a frame the control plane would reject is not written
        raise SystemExit("ERROR: generated frame violates TrailFrame contract: " + "; ".join(frame_errors))

    frame_rel = f".pmcro/trails/frames/{frame_id.removeprefix('frame-')}.json"
    rt.write_json(root / frame_rel, frame)

    event = {
        "event_id": rt.next_event_id(root),
        "cycle_id": message["cycle_id"],
        "phase": message["target"],
        "event_type": "phase-message-dispatched",
        "summary": frame["summary"],
        "evidence_refs": [frame_rel],
    }
    rt.append_event(root, event)

    entry = {
        "message_id": message["message_id"],
        "cycle_id": message["cycle_id"],
        "source": message["source"],
        "target": message["target"],
        "message_type": message["message_type"],
        "idempotency_key": message.get("idempotency_key", ""),
        "attempt": message.get("attempt", 1),
        "approved": bool(approved),
        "frame_ref": frame_rel,
        "payload_sha256": payload_sha256,
        "event_id": event["event_id"],
        "dispatched_utc": frame["created_utc"],
    }
    ledger.setdefault("dispatches", []).append(entry)
    rt.save_ledger(root, ledger)

    return {
        "status": "delivered",
        "message_id": message["message_id"],
        "target": message["target"],
        "frame_ref": frame_rel,
        "event_id": event["event_id"],
        "payload_sha256": payload_sha256,
    }


def update_checkpoint(root: pathlib.Path, path: pathlib.Path, message: dict, result: dict) -> list[str]:
    """Keep a cycle resumable: record what was delivered and what phase is owed."""
    checkpoint = rt.load_json(path)
    checkpoint["cycle_id"] = message["cycle_id"]
    checkpoint["last_completed_phase"] = message["source"]
    checkpoint["next_phase"] = message["target"]
    checkpoint["pending_message_id"] = message["message_id"]
    checkpoint["last_frame_id"] = "frame-" + pathlib.Path(result["frame_ref"]).stem
    checkpoint["last_frame_hash"] = result["payload_sha256"]
    attempts = checkpoint.setdefault("attempts", {})
    attempts[message["target"]] = attempts.get(message["target"], 0) + 1
    checkpoint["status"] = "resumable"
    errors = rt.validate_against(root, checkpoint, "checkpoint.schema.json")
    if not errors:
        rt.write_json(path, checkpoint)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch a typed PMCRO PhaseMessage.")
    parser.add_argument("message", help="path to a PhaseMessage JSON file")
    parser.add_argument("--root", default=None, help="repository root (defaults to the enclosing .pmcro owner)")
    parser.add_argument("--approved", action="store_true", help="a human authorized a message marked requires_approval")
    parser.add_argument("--checkpoint", default=None, help="checkpoint file to update after a delivered dispatch")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve() if args.root else rt.find_root(pathlib.Path(args.message))
    message = rt.load_json(args.message)
    code, result = dispatch(root, message, approved=args.approved)

    if code == EXIT_OK and result["status"] == "delivered" and args.checkpoint:
        checkpoint_errors = update_checkpoint(root, pathlib.Path(args.checkpoint), message, result)
        if checkpoint_errors:
            result["checkpoint_errors"] = checkpoint_errors

    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
