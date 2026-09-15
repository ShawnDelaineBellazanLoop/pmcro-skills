#!/usr/bin/env python3
"""Tests for crash-resilient claims and the editor-boundary policy gate.

Two things are being proven here. First, that an unplanned shutdown leaves a
readable record of what was in flight. Second, that the policy table is enforced
where writes actually happen, not only when someone politely goes through the
script - and that the gate fails OPEN on its own bugs, because a guard that can
break the session is a guard that gets removed.

Run: python .pmcro/tests/test_hooks_checkpoint.py
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / ".pmcro" / "scripts"))

import checkpoint as cp  # noqa: E402

# The guard ships with the plugin, so it lives under the plugin root rather than
# repository-local .claude: installing the plugin elsewhere carries the gate with
# it, and this repository's own settings point at that same file.
GUARD = REPO / "plugins" / "pmcro" / "scripts" / "control_plane_guard.py"


class ClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="pmcro-claims-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        (self.tmp / ".pmcro" / "state").mkdir(parents=True)

    def test_a_claim_survives_as_the_record_of_what_was_attempted(self) -> None:
        entry = cp.claim(self.tmp, "rebuild the dispatcher", "session", "cyc-x")
        self.assertIsNone(entry["closed_utc"])
        state = cp.status(self.tmp)
        self.assertEqual(len(state["open"]), 1)
        self.assertEqual(state["open"][0]["description"], "rebuild the dispatcher")

    def test_a_heartbeat_records_progress_without_unbounded_growth(self) -> None:
        cp.claim(self.tmp, "long job", "session", None)
        for index in range(30):
            cp.beat(self.tmp, "session", f"file-{index}.txt")
        touched = cp.status(self.tmp)["open"][0]["touched"]
        self.assertEqual(len(touched), 20, "the heartbeat is a sign of life, not a file log")
        self.assertEqual(touched[-1], "file-29.txt")

    def test_a_repeated_path_moves_to_the_end_instead_of_duplicating(self) -> None:
        cp.claim(self.tmp, "edits", "session", None)
        cp.beat(self.tmp, "session", "a.txt")
        cp.beat(self.tmp, "session", "b.txt")
        cp.beat(self.tmp, "session", "a.txt")
        self.assertEqual(cp.status(self.tmp)["open"][0]["touched"], ["b.txt", "a.txt"])

    def test_an_unreleased_claim_becomes_abandoned_not_deleted(self) -> None:
        """A shutdown leaves an open claim; the next run must not erase that fact."""
        cp.claim(self.tmp, "interrupted work", "session", None)
        cp.claim(self.tmp, "next work", "session", None)
        state = cp.status(self.tmp)
        self.assertEqual(len(state["open"]), 1)
        self.assertEqual(state["abandoned_count"], 1)
        self.assertEqual(state["last_abandoned"]["description"], "interrupted work")

    def test_release_closes_the_claim_with_an_outcome(self) -> None:
        cp.claim(self.tmp, "finishable work", "session", None)
        entry = cp.release(self.tmp, "session", "done", "all tests green")
        self.assertEqual(entry["outcome"], "done")
        self.assertEqual(cp.status(self.tmp)["open"], [])

    def test_a_truncated_claims_file_does_not_stop_the_next_run(self) -> None:
        """Half-written JSON is exactly what an abrupt power loss leaves behind."""
        cp.claims_path(self.tmp).write_text('{"version": 1, "claims": [{"owner"', encoding="utf-8")
        entry = cp.claim(self.tmp, "after the crash", "session", None)
        self.assertEqual(entry["description"], "after the crash")


class ControlPlaneGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="pmcro-guard-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        control = self.tmp / ".pmcro"
        shutil.copytree(REPO / ".pmcro" / "policies", control / "policies")
        (control / "trails" / "frames").mkdir(parents=True)
        (control / "checkpoints").mkdir(parents=True)
        (control / "laws").mkdir(parents=True)
        (control / "trails" / "frames" / "existing.json").write_text("{}", encoding="utf-8")
        (control / "checkpoints" / "existing.json").write_text("{}", encoding="utf-8")
        (control / "laws" / "constitution.md").write_text("# laws", encoding="utf-8")

    def guard(self, tool: str, relative: str) -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": str(self.tmp / relative)}})
        environment = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.tmp)}
        return subprocess.run(
            [sys.executable, str(GUARD)], input=payload, capture_output=True, text=True, env=environment,
        )

    def test_editing_an_existing_frame_is_blocked(self) -> None:
        result = self.guard("Edit", ".pmcro/trails/frames/existing.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("LAW-010", result.stderr)

    def test_overwriting_an_existing_frame_with_write_is_also_blocked(self) -> None:
        """Replacing a file wholesale is an update whatever the tool is called."""
        result = self.guard("Write", ".pmcro/trails/frames/existing.json")
        self.assertEqual(result.returncode, 2)

    def test_writing_a_new_frame_is_allowed(self) -> None:
        result = self.guard("Write", ".pmcro/trails/frames/brand-new.json")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_changing_a_law_asks_for_a_person(self) -> None:
        result = self.guard("Edit", ".pmcro/laws/constitution.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("authorize", result.stderr)

    def test_advancing_a_checkpoint_is_allowed(self) -> None:
        result = self.guard("Edit", ".pmcro/checkpoints/existing.json")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_file_outside_the_control_plane_is_none_of_its_business(self) -> None:
        result = self.guard("Edit", "README.md")
        self.assertEqual(result.returncode, 0)

    def guard_without_env(self, relative: str) -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(self.tmp / relative)}})
        environment = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "PMCRO_PROJECT_DIR")}
        return subprocess.run(
            [sys.executable, str(GUARD)], input=payload, capture_output=True, text=True,
            env=environment, cwd=str(REPO),
        )

    def test_the_gate_works_with_no_harness_variable_set(self) -> None:
        """CLAUDE_PROJECT_DIR is the host's name and cannot be renamed.

        Depending on it would mean the gate silently stops working under any
        other harness, so the script walks up from the file being written to
        find the control plane instead. Note cwd is deliberately a different
        repository here: only the target path can lead it to the right root.
        """
        result = self.guard_without_env(".pmcro/trails/frames/existing.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("LAW-010", result.stderr)

    def test_a_neutral_override_is_honored_first(self) -> None:
        payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(self.tmp / ".pmcro/laws/constitution.md")}})
        environment = {**os.environ, "PMCRO_PROJECT_DIR": str(self.tmp)}
        environment.pop("CLAUDE_PROJECT_DIR", None)
        result = subprocess.run(
            [sys.executable, str(GUARD)], input=payload, capture_output=True, text=True, env=environment,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("authorize", result.stderr)

    def test_malformed_input_fails_open(self) -> None:
        """A broken gate must not break the session; it fails open and says so."""
        environment = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.tmp)}
        result = subprocess.run(
            [sys.executable, str(GUARD)], input="not json at all", capture_output=True, text=True, env=environment,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
