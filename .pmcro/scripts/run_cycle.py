#!/usr/bin/env python3
"""Run a bounded forward-only PMCRO cycle using JSON phase files.

This runner is an orchestration boundary, not an LLM. Phase agents may be
connected by an adapter that writes the next envelope to the cycle directory.
"""
from __future__ import annotations
import argparse, json, pathlib, shutil, time

ORDER = ["planner", "maker", "checker", "reflector", "orchestrator"]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycle-dir", required=True)
    parser.add_argument("--max-cycles", type=int, default=5)
    args = parser.parse_args()
    root = pathlib.Path(args.cycle_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    state = {"cycle": 1, "phase": "planner", "status": "running", "started": time.time()}
    for cycle in range(1, args.max_cycles + 1):
        state["cycle"] = cycle
        for phase in ORDER:
            state["phase"] = phase
            marker = root / f"cycle-{cycle:03d}-{phase}.json"
            if not marker.exists():
                state["status"] = "waiting"
                (root / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
                print(json.dumps({"status": "waiting", "required": str(marker), "cycle": cycle, "phase": phase}))
                return 2
            state["last_completed"] = str(marker)
        decision = json.loads((root / f"cycle-{cycle:03d}-orchestrator.json").read_text(encoding="utf-8"))
        verdict = decision.get("verdict")
        if verdict in {"ACCEPT", "ESCALATE", "INTERRUPT"}:
            state["status"] = verdict.lower()
            (root / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
            print(json.dumps(state))
            return 0 if verdict == "ACCEPT" else 3
    state["status"] = "cycle-limit"
    (root / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(json.dumps(state))
    return 3

if __name__ == "__main__": raise SystemExit(main())
