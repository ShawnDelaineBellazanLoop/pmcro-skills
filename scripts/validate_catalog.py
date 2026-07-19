#!/usr/bin/env python3
"""
validate_catalog.py

CI gate for the PMCRO Skills catalog. Enforces:
  1. catalog/skills.json conforms to catalog/skills.schema.json
  2. every indexed skill's `path` exists on disk
  3. every indexed skill folder has manifest.json + SKILL.md
  4. SKILL.md frontmatter (name/description) matches the index entry
  5. no duplicate `name` values in the index

Exit code 0 = pass, 1 = fail (fails CI on any violation).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_JSON = ROOT / "catalog" / "skills.json"
CATALOG_SCHEMA = ROOT / "catalog" / "skills.schema.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        if line.startswith(("name:", "description:", "compatibility:")):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
        elif key and line.strip():
            # continuation of a multi-line quoted value; best-effort only
            fm[key] += " " + line.strip().strip('"')
    return fm


def main() -> int:
    errors: list[str] = []

    if not CATALOG_JSON.exists():
        print(f"ERROR: {CATALOG_JSON} not found", file=sys.stderr)
        return 1
    if not CATALOG_SCHEMA.exists():
        print(f"ERROR: {CATALOG_SCHEMA} not found", file=sys.stderr)
        return 1

    catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    schema = json.loads(CATALOG_SCHEMA.read_text(encoding="utf-8"))

    try:
        jsonschema.validate(instance=catalog, schema=schema)
    except jsonschema.ValidationError as e:
        fail(f"skills.json failed schema validation: {e.message}", errors)

    seen_names: set[str] = set()
    for entry in catalog.get("skills", []):
        name = entry.get("name", "<unnamed>")

        if name in seen_names:
            fail(f"[{name}] duplicate name in catalog index", errors)
        seen_names.add(name)

        skill_dir = ROOT / entry["path"]
        if not skill_dir.exists():
            fail(f"[{name}] path does not exist: {skill_dir}", errors)
            continue

        manifest_path = skill_dir / "manifest.json"
        skill_md_path = skill_dir / "SKILL.md"

        if not manifest_path.exists():
            fail(f"[{name}] missing manifest.json at {manifest_path}", errors)
        if not skill_md_path.exists():
            fail(f"[{name}] missing SKILL.md at {skill_md_path}", errors)
            continue

        fm = parse_frontmatter(skill_md_path)
        if fm.get("name") != name:
            fail(
                f"[{name}] SKILL.md frontmatter name='{fm.get('name')}' "
                f"does not match catalog entry name='{name}'",
                errors,
            )
        if not fm.get("description"):
            fail(f"[{name}] SKILL.md frontmatter missing description", errors)

    if errors:
        print(f"FAIL — {len(errors)} issue(s):\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"OK — {len(catalog.get('skills', []))} skill(s) validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
