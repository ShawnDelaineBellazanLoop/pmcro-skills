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
