#!/usr/bin/env python3
"""Validate basic Agent Skills structure and relative resource links."""
from __future__ import annotations
import argparse, pathlib, re

NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK = re.compile(r"\]\(([^)]+)\)")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_path")
    args = parser.parse_args()
    root = pathlib.Path(args.skill_path).expanduser().resolve()
    skill = root / "SKILL.md"
    errors = []
    if not NAME.fullmatch(root.name) or len(root.name) > 64:
        errors.append("directory name is not Agent Skills compliant")
    if not skill.is_file():
        errors.append("missing SKILL.md")
    else:
        text = skill.read_text(encoding="utf-8")
        if len(text.splitlines()) > 500:
            errors.append("SKILL.md exceeds 500 lines")
        if not text.startswith("---\n") or "name:" not in text.split("---", 2)[1] or "description:" not in text.split("---", 2)[1]:
            errors.append("frontmatter must contain name and description")
        for target in LINK.findall(text):
            if "://" not in target and not target.startswith("#") and not (root / target).is_file():
                errors.append(f"missing linked resource: {target}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"VALID: {root}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
