#!/usr/bin/env python3
"""
validate_skill.py

Validates a single skill folder against the pmcro-skills anatomy convention.
Lighter-weight than the repo-root scripts/validate_catalog.py — use this while
authoring one skill; use validate_catalog.py before opening a PR (it also checks
the skill is correctly indexed in catalog/skills.json).

Usage:
    python3 validate_skill.py <path-to-skill-folder>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
REQUIRED_SECTIONS = [
    "## Trigger On",
    "## Value",
    "## Do Not Use For",
    "## Inputs",
    "## Quick Start",
    "## Workflow",
    "## Deliver",
    "## Validate",
    "## Required Result Format",
    "## Load References",
    "## Example Requests",
]
PLACEHOLDER_RE = re.compile(r"<[a-zA-Z][a-zA-Z0-9 _-]*>|\{[a-zA-Z][a-zA-Z0-9 _-]*\}|TODO")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 validate_skill.py <path-to-skill-folder>", file=sys.stderr)
        return 1

    skill_dir = Path(sys.argv[1]).resolve()
    errors: list[str] = []

    manifest = skill_dir / "manifest.json"
    skill_md = skill_dir / "SKILL.md"

    if not manifest.exists():
        errors.append(f"missing manifest.json at {manifest}")
    if not skill_md.exists():
        errors.append(f"missing SKILL.md at {skill_md}")
        print("\n".join(f"  - {e}" for e in errors), file=sys.stderr)
        return 1

    text = skill_md.read_text(encoding="utf-8")

    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        errors.append("SKILL.md has no valid YAML frontmatter block")
    else:
        fm = fm_match.group(1)
        if "name:" not in fm:
            errors.append("frontmatter missing 'name'")
        if "description:" not in fm:
            errors.append("frontmatter missing 'description'")
        elif not re.search(r"USE FOR:.*DO NOT USE FOR:.*INVOKES:", fm, re.DOTALL):
            errors.append(
                "description does not follow the 'USE FOR / DO NOT USE FOR / INVOKES' pattern"
            )
        if skill_dir.name and f"name: {skill_dir.name}" not in fm:
            errors.append(
                f"frontmatter 'name' does not match folder name '{skill_dir.name}'"
            )

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing required section: {section}")

    placeholders = PLACEHOLDER_RE.findall(text)
    if placeholders:
        errors.append(f"placeholder text remaining: {sorted(set(placeholders))}")

    # only scripts/, references/, assets/ are recognized subfolders
    allowed = {"scripts", "references", "assets"}
    for child in skill_dir.iterdir():
        if child.is_dir() and child.name not in allowed:
            errors.append(
                f"unrecognized subfolder '{child.name}' — MAF only reads "
                f"scripts/, references/, assets/"
            )

    if errors:
        print(f"FAIL — {len(errors)} issue(s) in {skill_dir}:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"OK — {skill_dir} is catalog-compliant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
