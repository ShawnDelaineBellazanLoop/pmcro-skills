#!/usr/bin/env python3
"""Crash-resilient checkpointing: claim work, record progress, survive a shutdown.

A checkpoint written only at the end of a cycle is worth nothing to a machine
that sleeps mid-cycle. So this keeps two things:

  the claim   - what is in flight right now, written before the work starts
  the beat    - when the control plane was last touched, written after each step

If the process dies, the claim is still there, and whoever resumes reads what was
being attempted instead of reconstructing it from a transcript that is gone.

Claims live in .pmcro/state/claims.json rather than in the checkpoint files,
because CheckpointSchema forbids extra fields and 'what is in flight' is
execution state, not the resumable phase record.

Commands:
  claim "<what>"     open a claim (replaces any stale claim with the same owner)
  release [--note]   close the open claim
  beat               touch the heartbeat; used by the editor hook after each write
  status             print the current claim and heartbeat
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pmcro_runtime as rt  # noqa: E402

DEFAULT_OWNER = "session"


def claims_path(root: pathlib.Path) -> pathlib.Path:
    return root / rt.CONTROL_PLANE / "state" / "claims.json"


def load_claims(root: pathlib.Path) -> dict:
    path = claims_path(root)
    if path.exists():
        try:
            return rt.load_json(path)
        except json.JSONDecodeError:
            # A half-written file is exactly what an abrupt shutdown leaves. Losing
            # the claim is bad; refusing to run afterwards is worse.
            return {"version": 1, "claims": [], "recovered_from_corruption": True}
    return {"version": 1, "claims": []}


def save_claims(root: pathlib.Path, document: dict) -> pathlib.Path:
    """Write through a temp file so a shutdown mid-write cannot truncate the record."""
    path = claims_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)
    return path


def open_claim(document: dict, owner: str) -> dict | None:
    return next((c for c in document["claims"] if c["owner"] == owner and c.get("closed_utc") is None), None)


def claim(root: pathlib.Path, description: str, owner: str, cycle_id: str | None) -> dict:
    document = load_claims(root)
    existing = open_claim(document, owner)
    if existing:
        # A still-open claim from a previous run means that run did not finish.
        # Keep it in the record as abandoned rather than deleting the evidence.
        existing["closed_utc"] = rt.utc_now()
        existing["outcome"] = "abandoned"
        existing["note"] = "superseded by a new claim; the previous run did not release it"
    entry = {
        "claim_id": str(uuid.uuid4()),
        "owner": owner,
        "description": description,
        "cycle_id": cycle_id,
        "opened_utc": rt.utc_now(),
        "closed_utc": None,
        "outcome": None,
        "heartbeat_utc": rt.utc_now(),
        "touched": [],
    }
    document["claims"].append(entry)
    save_claims(root, document)
    return entry


def release(root: pathlib.Path, owner: str, outcome: str, note: str | None) -> dict | None:
    document = load_claims(root)
    entry = open_claim(document, owner)
    if entry is None:
        return None
    entry["closed_utc"] = rt.utc_now()
    entry["outcome"] = outcome
    if note:
        entry["note"] = note
    save_claims(root, document)
    return entry


def beat(root: pathlib.Path, owner: str, touched: str | None) -> dict | None:
    """Record that work is still moving, and on what.

    The touched list is capped: a heartbeat is a sign of life, not a file log,
    and an unbounded list would make the recovery record harder to read than the
    thing it is meant to explain.
    """
    document = load_claims(root)
    entry = open_claim(document, owner)
    if entry is None:
        return None
    entry["heartbeat_utc"] = rt.utc_now()
    if touched:
        files = entry.setdefault("touched", [])
        if touched in files:
            files.remove(touched)
        files.append(touched)
        del files[:-20]
    save_claims(root, document)
    return entry


def status(root: pathlib.Path) -> dict:
    document = load_claims(root)
    open_claims = [c for c in document["claims"] if c.get("closed_utc") is None]
    abandoned = [c for c in document["claims"] if c.get("outcome") == "abandoned"]
    return {
        "open": open_claims,
        "abandoned_count": len(abandoned),
        "last_abandoned": abandoned[-1] if abandoned else None,
        "total": len(document["claims"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Claim, beat, and release PMCRO work claims.")
    parser.add_argument("command", choices=["claim", "release", "beat", "status"])
    parser.add_argument("description", nargs="?", default=None, help="what is being attempted (claim)")
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--cycle-id", default=None)
    parser.add_argument("--outcome", default="done", choices=["done", "failed", "abandoned"])
    parser.add_argument("--note", default=None)
    parser.add_argument("--touched", default=None, help="path touched by the step that just finished (beat)")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve() if args.root else rt.find_root(pathlib.Path(__file__))

    if args.command == "claim":
        if not args.description:
            parser.error("claim needs a description of what is being attempted")
        print(json.dumps(claim(root, args.description, args.owner, args.cycle_id), indent=2))
        return 0

    if args.command == "release":
        entry = release(root, args.owner, args.outcome, args.note)
        if entry is None:
            print(json.dumps({"status": "no-open-claim", "owner": args.owner}, indent=2))
            return 1
        print(json.dumps(entry, indent=2))
        return 0

    if args.command == "beat":
        entry = beat(root, args.owner, args.touched)
        # No open claim is not an error: plenty of work happens outside a claim,
        # and a hook that fails the tool call because of bookkeeping is a hook
        # someone will disable.
        print(json.dumps(entry or {"status": "no-open-claim"}, indent=2))
        return 0

    print(json.dumps(status(root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
