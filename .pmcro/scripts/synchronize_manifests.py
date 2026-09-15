#!/usr/bin/env python3
"""Check marketplace manifests contain the same plugin entries."""
from __future__ import annotations
import argparse, json, pathlib

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    args = parser.parse_args()
    root = pathlib.Path(args.root).expanduser().resolve()
    paths = [
        root / ".agents/plugins/marketplace.json",
        root / ".claude-plugin/marketplace.json",
        root / ".codex-plugin/marketplace.json",
        root / ".cursor-plugin/marketplace.json",
        root / ".github/plugin/marketplace.json",
    ]
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths if path.is_file()]
    if len(payloads) != len(paths):
        print("ERROR: one or more marketplace manifests are missing")
        return 1
    canonical = json.dumps(payloads[0].get("plugins", []), sort_keys=True)
    for path, payload in zip(paths[1:], payloads[1:]):
        if json.dumps(payload.get("plugins", []), sort_keys=True) != canonical:
            print(f"ERROR: plugin entries differ in {path}")
            return 1
    print(f"VALID: {len(paths)} marketplace manifests synchronized")
    return 0

if __name__ == "__main__": raise SystemExit(main())
