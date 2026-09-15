#!/usr/bin/env python3
"""PostToolUse hook: record a heartbeat after every write.

This is the answer to "what happens when the machine shuts down mid-work". A
checkpoint written at the end of a cycle is useless to a session that never
reaches the end. A heartbeat after each write costs nothing and means the most
that can be lost is the step in progress.

It never blocks. A bookkeeping hook that can fail a tool call is a hook someone
turns off, and then there is no checkpointing at all. Always exits 0.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from control_plane_guard import project_dir  # noqa: E402 - one root resolver, not two


def main() -> None:
    raw = sys.stdin.read().lstrip("﻿")
    payload = {}
    if raw.strip():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}

    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path")
    hint = None
    if target:
        try:
            hint = Path(str(target)).resolve().parent
        except (ValueError, OSError):
            hint = None
    root = project_dir(hint)

    touched = None
    if target:
        try:
            touched = Path(str(target)).resolve().relative_to(root).as_posix()
        except (ValueError, OSError):
            touched = str(target)

    command = [sys.executable, str(root / ".pmcro" / "scripts" / "checkpoint.py"), "beat", "--root", str(root)]
    if touched:
        command += ["--touched", touched]

    try:
        subprocess.run(command, capture_output=True, text=True, timeout=10)
    except Exception:  # noqa: BLE001 - a missed heartbeat is not worth a failed tool call
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
