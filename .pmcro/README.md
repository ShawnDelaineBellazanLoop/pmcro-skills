# PMCR-O Control Plane

This directory defines the operational contract for the Planner-Maker-Checker-Reflector-Orchestrator lifecycle.

## State flow

```text
Intent → Planner → Maker → Checker → Reflector → Orchestrator
```

Every result flows forward to Reflector before the Orchestrator decides the next cycle. No phase jumps backward directly.

## Production guarantees

- Typed JSON envelopes are the state-transfer boundary.
- The Checker validates external ground truth; it does not trust Maker claims.
- The Reflector records reusable constraints, not hidden chain-of-thought.
- The Orchestrator has bounded retries, approval gates, and escalation.
- Trails contain evidence, hashes, timestamps, and tool results.
- Laws are versioned and changes require explicit review.

## Contents

- [Laws](laws/constitution.md) - Immutable safety and lifecycle rules.
- [Schemas](schemas/intent-envelope.schema.json) - Machine-readable phase contracts.
- [Configuration](templates/pmcro.config.json) - Runtime defaults and limits.
- [Cycle runner](scripts/run_cycle.py) - Forward-only orchestration skeleton.
- [Trail recorder](scripts/record_trail.py) - Append-only audit events.
- [Envelope validator](scripts/validate_envelope.py) - Schema and phase checks.

## Runtime boundary

Only the Orchestrator runs these. Phase agents return typed messages; they do not
invoke scripts. All of it is stdlib Python.

- [Dispatcher](scripts/dispatch_message.py) - Delivers a PhaseMessage through five gates: envelope contract, forward-only routing, replay suppression by idempotency key, per-phase attempt bounds, and the approval hold.
- [Queue adapter](scripts/queue_adapter.py) - Durable pending/processing/done/held/dead queue with visibility leases and dead letters; the drain maps dispatcher exit codes to queue states.
- [Webhook ingress](scripts/ingress.py) - Bounds a payload, writes a low-confidence SeedIntent, and enqueues a message that requires approval unless the origin is trusted.
- [Host boundary preflight](scripts/validate_host_boundary.py) - Checks the MAF adapter obligations and the tool-authority boundary offline, and names what only a live host can verify.
- [Shared runtime helpers](scripts/pmcro_runtime.py) - Schema subset checker, canonical hashing, config loading, trail and ledger writes.
- [Content manifest](scripts/manifest.py) - Generates and verifies `MANIFEST.sha256`.

## Verification

`python .pmcro/tests/run_all.py` runs every offline check and reports each one
separately. Accepting on a partial check is how a cycle ends up certifying work
it never examined.
