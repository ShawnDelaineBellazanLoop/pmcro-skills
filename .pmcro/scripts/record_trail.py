#!/usr/bin/env python3
"""Append a hashed, timestamped event to the PMCRO JSONL trail."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, uuid
from datetime import datetime, timezone

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trail", required=True)
    parser.add_argument("--cycle-id", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--event-type", required=True)
    parser.add_argument("--payload", required=True)
    args = parser.parse_args()
    payload = json.loads(pathlib.Path(args.payload).read_text(encoding="utf-8"))
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    event = {"event_id": str(uuid.uuid4()), "cycle_id": args.cycle_id, "phase": args.phase, "event_type": args.event_type, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "payload_sha256": hashlib.sha256(raw).hexdigest(), "payload": payload}
    path = pathlib.Path(args.trail).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream: stream.write(json.dumps(event, sort_keys=True) + "\n")
    print(json.dumps({"event_id": event["event_id"], "trail": str(path), "payload_sha256": event["payload_sha256"]}))
    return 0

if __name__ == "__main__": raise SystemExit(main())
