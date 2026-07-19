#!/usr/bin/env python3
"""
validate_trails.py

Trail-integrity checker for catalog-check. Enforces, against everything already
sealed under .pmcro/trails/:

  TRAIL-001 checks (structural well-formedness of each trail):
    1. Every trail dir has 00-frame.json
    2. Every trail dir has at least one NN-plan/make/check.jsonl triplet
    3. Every trail dir has disposition.json, and it is valid JSON with the
       required keys (sealed_at, final_verdict, total_cycles, earned_constraints,
       open_hypotheses, next_seed_intent)

  PLAN-002 checks (against every NN-plan.jsonl line in every trail):
    4. Every plan step has a "skill" key present (even if null)
    5. If "skill" is not null, it must match a real "name" in catalog/skills.json
    6. If "skill" is null, "needs_new_skill" must be present (true or false)
    7. "skill" is never one of the five role names (orchestrator/planner/maker/
       checker/reflector) -- a step must never be routed to a role

Read-only. Never modifies anything under .pmcro/trails/ or catalog/.

Exit code 0 = pass, 1 = fail.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]  # .../catalog/Tools/Agent-Foundry/skills/catalog-check/scripts -> repo root
CATALOG_JSON = ROOT / "catalog" / "skills.json"
TRAILS_ROOT = ROOT / ".pmcro" / "trails"
ROLE_NAMES = {"orchestrator", "planner", "maker", "checker", "reflector"}
REQUIRED_DISPOSITION_KEYS = {
    "sealed_at", "final_verdict", "total_cycles",
    "earned_constraints", "open_hypotheses", "next_seed_intent",
}


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def load_catalog_skill_names() -> set[str]:
    if not CATALOG_JSON.exists():
        return set()
    data = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    return {entry["name"] for entry in data.get("skills", [])}


def check_trail(trail_dir: Path, catalog_names: set[str], errors: list[str]) -> None:
    trail_label = str(trail_dir.relative_to(TRAILS_ROOT))

    frame = trail_dir / "00-frame.json"
    if not frame.exists():
        fail(f"[{trail_label}] missing 00-frame.json", errors)
    else:
        try:
            json.loads(frame.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f"[{trail_label}] 00-frame.json is not valid JSON: {e}", errors)

    plan_files = sorted(trail_dir.glob("*-plan.jsonl"))
    if not plan_files:
        fail(f"[{trail_label}] no NN-plan.jsonl found -- trail has no plan", errors)

    for plan_file in plan_files:
        cycle = plan_file.name.split("-")[0]
        make_file = trail_dir / f"{cycle}-make.jsonl"
        check_file = trail_dir / f"{cycle}-check.jsonl"
        if not make_file.exists():
            fail(f"[{trail_label}] cycle {cycle} has a plan but no make.jsonl", errors)
        if not check_file.exists():
            fail(f"[{trail_label}] cycle {cycle} has a plan but no check.jsonl", errors)

        for lineno, line in enumerate(plan_file.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                step = json.loads(line)
            except json.JSONDecodeError as e:
                fail(f"[{trail_label}] {plan_file.name} line {lineno} is not valid JSON: {e}", errors)
                continue

            if "skill" not in step:
                fail(
                    f"[{trail_label}] {plan_file.name} line {lineno} (step {step.get('step', '?')}) "
                    f"missing required 'skill' field (PLAN-002)",
                    errors,
                )
                continue

            skill = step["skill"]
            if skill is not None:
                if skill in ROLE_NAMES:
                    fail(
                        f"[{trail_label}] {plan_file.name} line {lineno} (step {step.get('step', '?')}) "
                        f"'skill' names a role ('{skill}') instead of a catalog skill -- forbidden by PLAN-002",
                        errors,
                    )
                elif skill not in catalog_names:
                    fail(
                        f"[{trail_label}] {plan_file.name} line {lineno} (step {step.get('step', '?')}) "
                        f"'skill' names '{skill}', which is not in catalog/skills.json",
                        errors,
                    )
            else:
                if "needs_new_skill" not in step:
                    fail(
                        f"[{trail_label}] {plan_file.name} line {lineno} (step {step.get('step', '?')}) "
                        f"has skill: null but no 'needs_new_skill' field (PLAN-002)",
                        errors,
                    )

    disposition = trail_dir / "disposition.json"
    if not disposition.exists():
        # Not necessarily an error -- a trail can be mid-cycle, not yet sealed.
        return
    try:
        disp = json.loads(disposition.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"[{trail_label}] disposition.json is not valid JSON: {e}", errors)
        return
    missing_keys = REQUIRED_DISPOSITION_KEYS - disp.keys()
    if missing_keys:
        fail(f"[{trail_label}] disposition.json missing keys: {sorted(missing_keys)}", errors)


def main() -> int:
    errors: list[str] = []

    if not TRAILS_ROOT.exists():
        print(f"NOTE: {TRAILS_ROOT} does not exist -- no trails to check (not a failure).")
        return 0

    catalog_names = load_catalog_skill_names()
    if not catalog_names:
        print(f"WARNING: {CATALOG_JSON} not found or empty -- cannot validate 'skill' references against it.", file=sys.stderr)

    trail_dirs = [p for p in TRAILS_ROOT.glob("*/*") if p.is_dir()]
    if not trail_dirs:
        print(f"NOTE: {TRAILS_ROOT} exists but contains no trail directories.")
        return 0

    for trail_dir in sorted(trail_dirs):
        check_trail(trail_dir, catalog_names, errors)

    if errors:
        print(f"FAIL — {len(errors)} issue(s) across {len(trail_dirs)} trail(s):\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"OK — {len(trail_dirs)} trail(s) validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
