#!/usr/bin/env python3
"""Gate tests for generic resource CRUD.

The point of these is the refusals. Anyone can make create and read work; what
makes the control plane trustworthy is that a frame cannot be updated, a law
cannot be changed without a human, and a resource nobody added to the table gets
denied rather than waved through.

Run: python .pmcro/tests/test_resource_ops.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / ".pmcro" / "scripts"))

import pmcro_runtime as rt  # noqa: E402
import resource_ops as ops  # noqa: E402


def frame(**overrides) -> dict:
    base = {
        "type": "TrailFrame",
        "frame_id": "frame-test-001",
        "cycle_id": "cyc-test",
        "phase": "maker",
        "frame_type": "artifact",
        "summary": "A frame written by the resource operations test.",
        "created_utc": "2026-09-15T12:00:00Z",
    }
    base.update(overrides)
    return base


class ResourceOperationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="pmcro-resource-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        control = self.tmp / ".pmcro"
        for folder in ("schemas", "templates", "policies", "laws"):
            shutil.copytree(REPO / ".pmcro" / folder, control / folder)
        (control / "trails" / "frames").mkdir(parents=True)
        (control / "checkpoints").mkdir(parents=True)
        rt.write_json(
            control / "trails" / "constraints" / "earned-constraints.json",
            {"version": 1, "constraints": [{"id": "ARCH-001", "rule": "Keep layers separate.", "status": "active"}]},
        )

    def events(self) -> list[dict]:
        path = self.tmp / ".pmcro" / "trails" / "events.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_policy_table_covers_every_resource_and_verb(self) -> None:
        rows = ops.policy_table(ops.load_policy(self.tmp))
        self.assertGreaterEqual(len(rows), 8)
        for row in rows:
            for verb in ops.OPERATIONS:
                self.assertIn(row[verb], {"allow", "approval", "deny"}, row["resource"])

    def test_laws_read_lists_the_constitution(self) -> None:
        code, result = ops.run(self.tmp, "laws", "read")
        self.assertEqual(code, ops.EXIT_OK)
        ids = [law["id"] for law in result["laws"]]
        self.assertIn("LAW-001", ids)
        self.assertIn("LAW-010", ids)
        self.assertEqual(len(ids), len(set(ids)), "law ids must be unique")

    def test_reading_leaves_no_trace(self) -> None:
        """A read that writes an event would make the trail a log of curiosity."""
        ops.run(self.tmp, "laws", "read")
        ops.run(self.tmp, "constraints", "read")
        self.assertEqual(self.events(), [])

    def test_a_frame_cannot_be_updated_or_deleted(self) -> None:
        """LAW-010 in executable form: the trail is append-only or it is not evidence."""
        for operation in ("update", "delete"):
            code, result = ops.run(self.tmp, "frames", operation, identifier="frame-test-001", payload=frame())
            self.assertEqual(code, ops.EXIT_DENIED, operation)
            self.assertEqual(result["status"], "denied")
            self.assertIn("LAW-010", result["reason"])
        self.assertEqual(self.events(), [])

    def test_a_frame_can_be_created_and_read(self) -> None:
        code, result = ops.run(self.tmp, "frames", "create", payload=frame())
        self.assertEqual(code, ops.EXIT_OK, result)
        self.assertTrue((self.tmp / result["path"]).exists())
        code, read_back = ops.run(self.tmp, "frames", "read", identifier="frame-test-001")
        self.assertEqual(code, ops.EXIT_OK)
        self.assertEqual(read_back["record"]["summary"], frame()["summary"])

    def test_a_frame_violating_its_contract_is_refused(self) -> None:
        code, result = ops.run(self.tmp, "frames", "create", payload=frame(frame_type="nonsense"))
        self.assertEqual(code, ops.EXIT_INPUT)
        self.assertTrue(any("frame_type" in error for error in result["errors"]))

    def test_changing_a_law_waits_for_a_human(self) -> None:
        """LAW-008: governance changes are the case the approval gate exists for."""
        payload = {"rule": "Trail events are append-only, and corrections reference the prior event."}
        code, result = ops.run(self.tmp, "laws", "update", identifier="LAW-010", payload=payload)
        self.assertEqual(code, ops.EXIT_APPROVAL)
        self.assertEqual(result["status"], "approval-required")
        original = (self.tmp / ".pmcro" / "laws" / "constitution.md").read_text(encoding="utf-8")
        self.assertIn("is not silently rewritten", original)

        code, result = ops.run(self.tmp, "laws", "update", identifier="LAW-010", payload=payload, approved=True)
        self.assertEqual(code, ops.EXIT_OK, result)
        changed = (self.tmp / ".pmcro" / "laws" / "constitution.md").read_text(encoding="utf-8")
        self.assertIn("corrections reference the prior event", changed)
        self.assertEqual(len(self.events()), 1, "an approved governance change records itself")

    def test_a_law_can_never_be_deleted(self) -> None:
        code, result = ops.run(self.tmp, "laws", "delete", identifier="LAW-001", approved=True)
        self.assertEqual(code, ops.EXIT_DENIED)
        self.assertIn("superseded", result["reason"])

    def test_a_constraint_is_created_freely_but_promoted_under_review(self) -> None:
        code, _ = ops.run(self.tmp, "constraints", "create", payload={"id": "ARCH-900", "rule": "Test rule.", "status": "candidate"})
        self.assertEqual(code, ops.EXIT_OK)

        code, result = ops.run(self.tmp, "constraints", "update", identifier="ARCH-900", payload={"status": "active"})
        self.assertEqual(code, ops.EXIT_APPROVAL)
        self.assertIn("constraint-promotion", result["reason"])

        code, result = ops.run(self.tmp, "constraints", "update", identifier="ARCH-900", payload={"status": "active"}, approved=True)
        self.assertEqual(code, ops.EXIT_OK)
        self.assertEqual(result["constraint"]["status"], "active")

    def test_a_constraint_is_retired_rather_than_deleted(self) -> None:
        code, result = ops.run(self.tmp, "constraints", "delete", identifier="ARCH-001", approved=True)
        self.assertEqual(code, ops.EXIT_DENIED)
        self.assertIn("Retire or supersede", result["reason"])

    def test_an_unknown_resource_is_denied_not_defaulted(self) -> None:
        code, result = ops.run(self.tmp, "secrets", "read")
        self.assertEqual(code, ops.EXIT_DENIED)
        self.assertIn("unknown resource", result["reason"])

    def test_a_governed_resource_without_a_store_says_so(self) -> None:
        """LAW-004: an unimplemented path escalates explicitly instead of pretending."""
        code, result = ops.run(self.tmp, "evidence", "create", payload={"id": "e-1"})
        self.assertEqual(code, ops.EXIT_NOT_IMPLEMENTED)
        self.assertEqual(result["status"], "not-implemented")

    def test_events_append_but_never_change(self) -> None:
        code, _ = ops.run(self.tmp, "events", "create", payload={"cycle_id": "cyc-test", "summary": "a recorded thing"})
        self.assertEqual(code, ops.EXIT_OK)
        self.assertEqual(len(self.events()), 1)
        code, result = ops.run(self.tmp, "events", "update", identifier="evt-001", payload={"summary": "rewritten"})
        self.assertEqual(code, ops.EXIT_DENIED)
        self.assertEqual(self.events()[0]["summary"], "a recorded thing")

    def test_a_checkpoint_advances_because_that_is_its_job(self) -> None:
        checkpoint = {
            "checkpoint_id": "checkpoint-test", "cycle_id": "cyc-test", "last_completed_phase": "maker",
            "next_phase": "checker", "last_frame_id": "frame-test-001", "status": "resumable",
        }
        self.assertEqual(ops.run(self.tmp, "checkpoints", "create", payload=checkpoint)[0], ops.EXIT_OK)
        code, _ = ops.run(self.tmp, "checkpoints", "update", identifier="checkpoint-test", payload={"next_phase": "reflector"})
        self.assertEqual(code, ops.EXIT_OK)
        code, result = ops.run(self.tmp, "checkpoints", "read", identifier="checkpoint-test")
        self.assertEqual(result["record"]["next_phase"], "reflector")


if __name__ == "__main__":
    unittest.main(verbosity=2)
