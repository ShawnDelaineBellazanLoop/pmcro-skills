#!/usr/bin/env python3
"""Gate tests for the PhaseMessage dispatcher.

Each test names the law it protects. The tests run against a throwaway copy of
the control plane, because a test that appends to the real Trail would make the
Trail a record of tests rather than of work (LAW-010).

Run: python .pmcro/tests/test_dispatch.py
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

import dispatch_message as dm  # noqa: E402
import pmcro_runtime as rt  # noqa: E402


def message(**overrides) -> dict:
    base = {
        "type": "PhaseMessage",
        "message_id": "msg-001",
        "cycle_id": "cyc-test-001",
        "source": "system",
        "target": "planner",
        "message_type": "seed-intent",
        "idempotency_key": "key-001",
        "attempt": 1,
    }
    base.update(overrides)
    return base


class DispatchGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="pmcro-dispatch-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        control = self.tmp / ".pmcro"
        shutil.copytree(REPO / ".pmcro" / "schemas", control / "schemas")
        shutil.copytree(REPO / ".pmcro" / "templates", control / "templates")
        (control / "trails" / "frames").mkdir(parents=True)

    def events(self) -> list[dict]:
        path = self.tmp / ".pmcro" / "trails" / "events.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_forward_edge_is_delivered_with_evidence(self) -> None:
        code, result = dm.dispatch(self.tmp, message())
        self.assertEqual(code, dm.EXIT_OK)
        self.assertEqual(result["status"], "delivered")
        self.assertTrue((self.tmp / result["frame_ref"]).exists())
        self.assertEqual(len(self.events()), 1)
        frame = rt.load_json(self.tmp / result["frame_ref"])
        self.assertEqual(rt.validate_against(self.tmp, frame, "trail-frame.schema.json"), [])

    def test_backward_edge_is_refused(self) -> None:
        """LAW-001: a failed check flows forward to reflector, not back to maker."""
        code, result = dm.dispatch(self.tmp, message(source="checker", target="maker"))
        self.assertEqual(code, dm.EXIT_ROUTING)
        self.assertEqual(result["status"], "routing-violation")
        self.assertEqual(self.events(), [])

    def test_redelivery_of_the_same_key_delivers_once(self) -> None:
        """At-least-once transports replay; the ledger keeps replay harmless."""
        first_code, first = dm.dispatch(self.tmp, message())
        second_code, second = dm.dispatch(self.tmp, message(message_id="msg-001-retry"))
        self.assertEqual((first_code, second_code), (dm.EXIT_OK, dm.EXIT_OK))
        self.assertEqual(second["status"], "duplicate")
        self.assertEqual(second["frame_ref"], first["frame_ref"])
        self.assertEqual(len(self.events()), 1)

    def test_attempt_limit_escalates(self) -> None:
        """LAW-007: bounded autonomy means the third try is a decision, not a retry."""
        limit = rt.load_config(self.tmp)["max_phase_attempts"]
        for index in range(limit):
            code, _ = dm.dispatch(
                self.tmp,
                message(source="planner", target="maker", message_id=f"msg-m{index}", idempotency_key=f"key-m{index}", attempt=index + 1),
            )
            self.assertEqual(code, dm.EXIT_OK)
        code, result = dm.dispatch(
            self.tmp,
            message(source="planner", target="maker", message_id="msg-m-over", idempotency_key="key-m-over", attempt=limit + 1),
        )
        self.assertEqual(code, dm.EXIT_BOUNDS)
        self.assertEqual(result["verdict"], "ESCALATE")

    def test_approval_gate_holds_until_a_human_authorizes(self) -> None:
        """LAW-008: the human veto is a gate in the path, not a note in a report."""
        held = message(requires_approval=True)
        code, result = dm.dispatch(self.tmp, held)
        self.assertEqual(code, dm.EXIT_APPROVAL)
        self.assertEqual(result["status"], "approval-required")
        self.assertEqual(self.events(), [])
        code, result = dm.dispatch(self.tmp, held, approved=True)
        self.assertEqual(code, dm.EXIT_OK)
        self.assertEqual(result["status"], "delivered")

    def test_envelope_contract_is_enforced_before_routing(self) -> None:
        bad = message(target="maker")
        bad["slash_command"] = "/pmcro:maker"  # slash text is not the protocol
        code, result = dm.dispatch(self.tmp, bad)
        self.assertEqual(code, dm.EXIT_CONTRACT)
        self.assertTrue(any("slash_command" in error for error in result["errors"]))

    def test_reentering_planning_requires_a_new_cycle(self) -> None:
        dm.dispatch(self.tmp, message())
        code, _ = dm.dispatch(
            self.tmp,
            message(source="orchestrator", target="planner", message_id="msg-loop", idempotency_key="key-loop"),
        )
        self.assertEqual(code, dm.EXIT_ROUTING)
        code, result = dm.dispatch(
            self.tmp,
            message(source="orchestrator", target="planner", cycle_id="cyc-test-002", message_id="msg-next", idempotency_key="key-next"),
        )
        self.assertEqual(code, dm.EXIT_OK)
        self.assertEqual(result["status"], "delivered")

    def test_frames_are_hash_chained(self) -> None:
        """LAW-010: each frame names the one before it, so a silent edit shows up."""
        _, first = dm.dispatch(self.tmp, message())
        _, second = dm.dispatch(
            self.tmp,
            message(source="planner", target="maker", message_id="msg-002", idempotency_key="key-002"),
        )
        chained = rt.load_json(self.tmp / second["frame_ref"])
        self.assertEqual(chained["previous_frame_hash"], first["payload_sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
