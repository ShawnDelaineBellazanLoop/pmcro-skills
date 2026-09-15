#!/usr/bin/env python3
"""Run every check a Checker can run offline, and report each one separately.

One entry point matters here because partial verification is how a cycle ends up
accepting on the strength of whichever check happened to be run. Each step
reports its own exit code; the overall result is the worst of them.

Run: python .pmcro/tests/run_all.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".vs", "node_modules", "__pycache__", "queue"}

STEPS = [
    ("dispatch gates", [sys.executable, str(REPO / ".pmcro/tests/test_dispatch.py")]),
    ("ingress and queue gates", [sys.executable, str(REPO / ".pmcro/tests/test_ingress_queue.py")]),
    ("resource operation gates", [sys.executable, str(REPO / ".pmcro/tests/test_resource_ops.py")]),
    ("claims and editor-boundary gate", [sys.executable, str(REPO / ".pmcro/tests/test_hooks_checkpoint.py")]),
    ("host boundary preflight", [sys.executable, str(REPO / ".pmcro/scripts/validate_host_boundary.py"), "--problems-only"]),
    ("control-plane scripts compile", [sys.executable, "-m", "compileall", "-q", str(REPO / ".pmcro/scripts")]),
    ("marketplace manifests synchronized", [sys.executable, str(REPO / ".pmcro/scripts/synchronize_manifests.py"), str(REPO)]),
    ("content manifest current", [sys.executable, str(REPO / ".pmcro/scripts/manifest.py"), "--check"]),
]


def json_parses() -> tuple[int, str]:
    """Every tracked JSON file must parse: contracts, registries, frames, checkpoints."""
    bad: list[str] = []
    count = 0
    for path in REPO.rglob("*.json"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        count += 1
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:  # noqa: BLE001 - the message is the finding
            bad.append(f"{path.relative_to(REPO)}: {error}")
    detail = f"{count} JSON files parsed" if not bad else "\n".join(bad)
    return (0 if not bad else 1), detail


def trail_frames_valid() -> tuple[int, str]:
    """Frames are the evidence record, so they are held to their own contract."""
    sys.path.insert(0, str(REPO / ".pmcro" / "scripts"))
    import pmcro_runtime as rt

    legacy_path = REPO / ".pmcro" / "trails" / "legacy-frames.json"
    legacy = set(rt.load_json(legacy_path)["frames"]) if legacy_path.exists() else set()

    problems: list[str] = []
    skipped = 0
    frames = sorted((REPO / ".pmcro" / "trails" / "frames").glob("*.json"))
    for frame_path in frames:
        errors = rt.validate_against(REPO, rt.load_json(frame_path), "trail-frame.schema.json")
        if not errors:
            continue
        if frame_path.name in legacy:
            # Recorded as history, not rewritten to match today's contract.
            skipped += 1
            continue
        problems.append(f"{frame_path.name}: {'; '.join(errors)}")
    detail = f"{len(frames) - skipped} TrailFrames valid, {skipped} LEGACY" if not problems else "\n".join(problems)
    return (0 if not problems else 1), detail


def checkpoints_valid() -> tuple[int, str]:
    sys.path.insert(0, str(REPO / ".pmcro" / "scripts"))
    import pmcro_runtime as rt

    problems: list[str] = []
    files = sorted((REPO / ".pmcro" / "checkpoints").glob("*.json"))
    for path in files:
        errors = rt.validate_against(REPO, rt.load_json(path), "checkpoint.schema.json")
        if errors:
            problems.append(f"{path.name}: {'; '.join(errors)}")
    detail = f"{len(files)} checkpoints valid" if not problems else "\n".join(problems)
    return (0 if not problems else 1), detail


def main() -> int:
    worst = 0
    for name, command in STEPS:
        completed = subprocess.run(command, capture_output=True, text=True)
        status = "PASS" if completed.returncode == 0 else "FAIL"
        worst = max(worst, completed.returncode)
        print(f"[{status}] {name} (exit {completed.returncode})")
        if completed.returncode != 0:
            print((completed.stdout + completed.stderr).strip()[:4000])

    for name, check in (("json parses", json_parses), ("trail frames valid", trail_frames_valid), ("checkpoints valid", checkpoints_valid)):
        code, detail = check()
        worst = max(worst, code)
        print(f"[{'PASS' if code == 0 else 'FAIL'}] {name}: {detail if code else detail}")

    print("OVERALL:", "PASS" if worst == 0 else "FAIL")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
