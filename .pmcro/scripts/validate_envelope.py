#!/usr/bin/env python3
"""Validate a PMCRO envelope against basic phase and required-field rules."""
from __future__ import annotations
import argparse, json, pathlib

PHASES = {"planner", "maker", "checker", "reflector", "orchestrator", "system"}
VERDICTS = {"ACCEPT", "EXTEND", "LOOP", "REJECT", "ESCALATE", "INTERRUPT"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope")
    args = parser.parse_args()
    path = pathlib.Path(args.envelope).expanduser().resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    for key in ("cycle_id", "phase"):
        if not data.get(key): errors.append(f"missing {key}")
    if data.get("phase") not in PHASES: errors.append("invalid phase")
    if data.get("verdict") and data["verdict"] not in VERDICTS: errors.append("invalid verdict")
    if data.get("phase") == "checker" and not data.get("findings"): errors.append("checker requires findings")
    if data.get("phase") == "reflector" and not data.get("earned_constraints"): errors.append("reflector requires earned_constraints")
    if errors:
        for error in errors: print(f"ERROR: {error}")
        return 1
    print(f"VALID: {path}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
