---
name: catalog-check
description: "USE FOR: validating that catalog/skills.json is internally consistent (schema-valid, every path exists, every skill has manifest.json + SKILL.md, frontmatter matches the index, no duplicate names); validating that sealed trails under .pmcro/trails/ are well-formed and that their plan frames comply with PLAN-002 (every step names a real catalog skill or is explicitly flagged needs_new_skill). DO NOT USE FOR: authoring or editing skill content itself -- that's skill-creator's job, this only checks what already exists. DO NOT USE FOR: deciding whether a LOOP-worthy finding should become an EarnedConstraint -- this skill reports findings, Reflector (if invoked) decides what binds. INVOKES: run the repo-root scripts/validate_catalog.py for catalog-index consistency, run this skill's own scripts/validate_trails.py for trail integrity, report both results together as one pass/fail summary."
compatibility: "Requires Python 3.12+ and jsonschema (shared with the repo-root scripts/validate_catalog.py, which this skill invokes rather than duplicates). Operates read-only -- never modifies catalog/skills.json, trail files, or any skill content."
---

# Catalog Check

## Trigger On

- "validate the catalog" / "check the catalog" / "something's off in skills.json"
- "check for duplicate skills" / "is my catalog consistent"
- "did I break a trail" / "check the trails" / "is this trail well-formed"
- Before registering a new skill in catalog/skills.json (sanity check first)

## Value

- One command answers both "is the skill index consistent" and "are my trails
  structurally sound and PLAN-002-compliant" instead of two separate manual checks.
- Reuses the repo-root `scripts/validate_catalog.py` as-is for catalog-index
  consistency (it already backs `.github/workflows/catalog-check.yml`) rather than
  forking a second copy of that logic inside this skill -- one source of truth for
  catalog validation, this skill only adds what didn't exist anywhere before: trail
  integrity checking.
- Read-only by design. Running this skill can never itself break something -- it can
  only report what's already broken.

## Do Not Use For

- Fixing anything it finds. This skill reports; skill-creator (for catalog/skill
  issues) or a human (for trail issues, since trails are immutable once sealed) acts.
- Deciding whether a finding rises to an EarnedConstraint. That's Reflector's job, and
  only after an actual LOOP verdict on a trail Checker is scoring -- catalog-check runs
  outside the PMCR-O cycle, as an audit tool, not as a cycle's own Checker.
- Validating anything outside `catalog/skills.json` and `.pmcro/trails/` -- it does not
  lint markdown prose, check spelling, or validate `.claude-plugin/marketplace.json`
  (that file currently has no owning skill at all -- a separate, still-open gap).

## Inputs

- None required for a full run -- both checks scan the whole repo from its root.
- Optional: a specific trail path, to check just one trail instead of every trail
  under `.pmcro/trails/`.

## Quick Start

1. Run `python3 scripts/validate_catalog.py` from the repo root (catalog-index check).
2. Run `python3 catalog/Tools/Agent-Foundry/skills/catalog-check/scripts/validate_trails.py`
   from the repo root (trail integrity check).
3. Report both exit codes and their full output together as one summary -- don't
   report only the first check and stop if it passes.

## Workflow

1. **Observe** — confirm `catalog/skills.json` and `.pmcro/trails/` both exist before
   running anything; report plainly if either is missing rather than erroring opaquely.
2. **Plan** — this skill has exactly two fixed checks, always both, every run. There is
   no partial-check mode beyond the optional single-trail input above.
3. **Create** — n/a, this skill produces no new files, only a report.
4. **Check** — run both scripts, capture stdout/stderr and exit codes from each.
5. **Reflect** — if either script fails to run at all (missing dependency, syntax
   error introduced by a bad edit), report that distinctly from "ran and found issues."
6. **Report** — a combined summary: catalog-index status, trail-integrity status, and
   the full list of specific issues found by either, not just pass/fail counts.

## Deliver

- Catalog-index result: OK or a list of specific violations (missing path, duplicate
  name, frontmatter mismatch, etc.), exactly as `scripts/validate_catalog.py` reports.
- Trail-integrity result: OK or a list of specific violations (malformed trail, plan
  step missing `skill`/`needs_new_skill`, step routing to a role instead of a skill),
  exactly as `scripts/validate_trails.py` reports.

## Validate

- Both scripts were actually executed, not assumed to pass because the files exist.
- The report distinguishes "check ran and passed," "check ran and found issues," and
  "check failed to run" — these are three different outcomes, not two.

## Ralph Loop

Run catalog-index check → run trail-integrity check → combine both real outputs into
one report → if either script itself errors out (not a validation failure, a crash),
report the crash and do not attempt to interpret partial output as a pass.

## Required Result Format

- `status`: `pass` | `fail` | `check_errored`
- `catalog_index`: `ok` | list of specific violations
- `trail_integrity`: `ok` | list of specific violations
- `remaining`: anything not covered by either check (e.g. marketplace.json has no
  validator), or `none`

## Load References

- [references/trail-integrity-checks.md](references/trail-integrity-checks.md) —
  exactly what `validate_trails.py` checks and why, one item per PLAN-002/TRAIL-001
  requirement.

## Example Requests

- "Validate the catalog before I commit."
- "Check if any trails are malformed."
- "Did the last trail actually comply with PLAN-002?"
- "Is skills.json still consistent after that last edit?"
