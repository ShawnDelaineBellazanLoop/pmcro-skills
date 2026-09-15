#!/usr/bin/env python3
"""Generate or verify MANIFEST.sha256, the content hash of the published tree.

The manifest is what lets someone who received this repository check that the
files are the files - a packaging integrity record, not a trail. It is therefore
regenerated whenever the tree changes, unlike frames and events, which are never
rewritten.

Excluded: version control and IDE state, caches, per-machine runtime state under
.pmcro/queue, and the manifest itself.

Run: python .pmcro/scripts/manifest.py --check   (exit 1 when stale)
     python .pmcro/scripts/manifest.py --write
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib

EXCLUDED_DIRS = {".git", ".vs", "node_modules", "__pycache__", ".pytest_cache"}
# .gitattributes and .gitignore are excluded to match the manifest already
# published for this tree. Widening what the manifest covers changes what a
# recipient is verifying, so that is a deliberate decision, not a side effect of
# adding a generator.
EXCLUDED_PATHS = {"MANIFEST.sha256", ".gitattributes", ".gitignore"}
# Runtime state, not published content. The queue holds per-machine jobs; state holds
# the live claim and its heartbeat, which changes on every write the editor hook sees.
# Covering either would make the manifest report itself stale during ordinary work, and a
# check that always fails is a check people learn to ignore.
EXCLUDED_PREFIXES = (".pmcro/queue/", ".pmcro/state/")


def tracked_files(root: pathlib.Path) -> list[pathlib.Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if relative in EXCLUDED_PATHS or relative.startswith(EXCLUDED_PREFIXES):
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def render(root: pathlib.Path) -> str:
    lines = []
    for path in tracked_files(root):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{path.relative_to(root).as_posix()}  {digest}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify MANIFEST.sha256.")
    parser.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parents[2]))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    manifest = root / "MANIFEST.sha256"
    rendered = render(root)

    if args.write:
        manifest.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"WROTE: {manifest.name} ({rendered.count(chr(10))} entries)")
        return 0

    current = manifest.read_text(encoding="utf-8") if manifest.exists() else ""
    if current == rendered:
        print(f"VALID: {manifest.name} matches the tree ({rendered.count(chr(10))} entries)")
        return 0

    current_map = dict(line.split("  ", 1)[::-1] for line in current.splitlines() if "  " in line)
    rendered_map = dict(line.split("  ", 1)[::-1] for line in rendered.splitlines() if "  " in line)
    current_paths = set(current_map.values())
    rendered_paths = set(rendered_map.values())
    print(f"STALE: {manifest.name}")
    for path in sorted(rendered_paths - current_paths):
        print(f"  added   {path}")
    for path in sorted(current_paths - rendered_paths):
        print(f"  removed {path}")
    changed = {p for p in current_paths & rendered_paths}
    inverse_current = {v: k for k, v in current_map.items()}
    inverse_rendered = {v: k for k, v in rendered_map.items()}
    for path in sorted(changed):
        if inverse_current[path] != inverse_rendered[path]:
            print(f"  changed {path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
