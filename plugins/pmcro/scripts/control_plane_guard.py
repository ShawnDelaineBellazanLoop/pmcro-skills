#!/usr/bin/env python3
"""PreToolUse gate: the resource policy, enforced against the editor's own tools.

resource_ops.py refuses to update a frame. That only helps when someone goes
through resource_ops.py. An agent with a Write tool can edit the same file
directly and the refusal never happens - so the policy table has to be enforced
where the write actually occurs.

This hook reads .pmcro/policies/resource-operations.json, the same file the skill
and the .NET runtime read, and blocks a Write or Edit that would perform an
operation the policy denies. One table, three enforcement points, no drift.

Create versus update is decided by whether the file already exists: writing a new
frame is 'create' (allowed); changing one already on disk is 'update' (denied for
frames, events, and evidence).

Exit 2 blocks and returns the reason to the agent. Exit 1 means this script hit
its own bug: it fails OPEN on those, and CLOSED only on policy.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BLOCK = 2
ALLOW = 0

POLICY_REL = ".pmcro/policies/resource-operations.json"


def project_dir(hint: Path | None = None) -> Path:
    """Find the repository without depending on any one harness's variable.

    CLAUDE_PROJECT_DIR is set by Claude Code and cannot be renamed or aliased -
    the host chooses the name. Depending on it would mean this gate silently
    stops working under Gemini, Cursor, a git hook, or CI, where nothing sets it.

    So the order is: an explicit neutral override, then the harness variable if
    it happens to be there, then a walk upward from the file being written (or
    the working directory) looking for the control plane. The last one needs no
    environment at all, which is why it exists.
    """
    for name in ("PMCRO_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        value = os.environ.get(name)
        if value:
            return Path(value).resolve()

    start = (hint or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".pmcro").is_dir():
            return candidate
    return Path.cwd().resolve()


def read_payload() -> dict:
    raw = sys.stdin.read().lstrip("﻿")  # a BOM would silently fail the gate open
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def block(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(BLOCK)


def resource_for(relative: str, resources: dict) -> tuple[str, dict] | None:
    """Longest declared path wins, so a nested resource is not shadowed by its parent."""
    best: tuple[str, dict] | None = None
    for name, entry in resources.items():
        declared = str(entry.get("path", "")).strip("/")
        if not declared:
            continue
        if relative == declared or relative.startswith(declared + "/"):
            if best is None or len(declared) > len(str(resources[best[0]].get("path", ""))):
                best = (name, entry)
    return best


def main() -> None:
    payload = read_payload()
    tool = str(payload.get("tool_name") or payload.get("tool") or "")
    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path")
    if not target:
        sys.exit(ALLOW)

    try:
        path = Path(str(target)).resolve()
    except (ValueError, OSError):
        sys.exit(ALLOW)

    # The file being written is the best hint for locating the control plane when
    # no harness variable is set.
    root = project_dir(path.parent)
    try:
        relative = path.relative_to(root).as_posix()
    except (ValueError, OSError):
        sys.exit(ALLOW)  # outside the project is not this gate's business

    policy_file = root / POLICY_REL
    if not policy_file.is_file():
        sys.exit(ALLOW)

    try:
        policy = json.loads(policy_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        sys.exit(ALLOW)

    match = resource_for(relative, policy.get("resources", {}))
    if match is None:
        sys.exit(ALLOW)

    name, entry = match
    # Edit always modifies something that exists. Write creates unless the file is
    # already there, in which case it replaces - which is an update by any honest
    # reading, whatever the tool is called.
    operation = "update" if (tool.lower().startswith("edit") or path.exists()) else "create"
    rule = entry.get(operation, {})

    if rule.get("decision") == "deny":
        block(
            f"BLOCKED by control_plane_guard: {operation} on '{name}' is denied.\n"
            f"{rule.get('reason', '')}\n"
            f"Target: {relative}\n"
            f"The policy is .pmcro/policies/resource-operations.json. Do not edit the file "
            f"directly to get around this - record a new entry that references the old one."
        )

    if rule.get("decision") == "approval":
        block(
            f"BLOCKED by control_plane_guard: {operation} on '{name}' needs a person to authorize it.\n"
            f"{rule.get('reason', '')}\n"
            f"Target: {relative}\n"
            f"Ask, then go through: python .pmcro/scripts/resource_ops.py {name} {operation} --approved"
        )

    sys.exit(ALLOW)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - a broken gate must not break the session
        print(f"control_plane_guard internal error (allowing): {exc}", file=sys.stderr)
        sys.exit(1)
