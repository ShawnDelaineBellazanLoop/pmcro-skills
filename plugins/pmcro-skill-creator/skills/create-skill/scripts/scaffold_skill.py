#!/usr/bin/env python3
"""Create a minimal MAF-compatible skill package without overwriting files."""
from __future__ import annotations
import argparse, pathlib, re

NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TEMPLATE = """---
name: {name}
description: \"{description}\"
license: MIT
compatibility: \"Document runtime requirements here.\"
metadata:
  version: \"0.1.0\"
---

# Purpose

Describe the outcome this skill produces.

## When to Use

- State concrete triggers.

## When Not to Use

- State the nearest boundary.

## Workflow

1. Plan inputs and side effects.
2. Read only the required bundled resources.
3. Run approved scripts and verify postconditions.

## Validation

Define observable success and truthful failure behavior.

## Bundled Resources

Link every file that the workflow requires with a relative Markdown path.
"""

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--root", required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()
    if not NAME.fullmatch(args.name) or len(args.name) > 64:
        raise SystemExit("invalid skill name: use lowercase letters, numbers, and single hyphens")
    root = pathlib.Path(args.root).expanduser().resolve() / args.name
    if root.exists():
        raise SystemExit(f"refusing to overwrite existing path: {root}")
    root.mkdir(parents=True)
    (root / "SKILL.md").write_text(TEMPLATE.format(name=args.name, description=args.description), encoding="utf-8")
    for folder in ("assets", "references", "scripts"):
        (root / folder).mkdir()
    print(root)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
