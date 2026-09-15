# Checkpointing and resume

Trail and checkpointing are complementary.

- **Trail:** append-only history of evidence, frames, decisions, and constraints.
- **Checkpoint:** mutable resume pointer identifying the last completed phase and next pending message.

A checkpoint must reference a TrailFrame and include cycle ID, pending message ID, attempts, status, and frame hash. On resume, the Orchestrator verifies the referenced frame and idempotency key before dispatching work. If verification fails, emit `ESCALATE` or `INTERRUPT`; never resume from an unverified pointer.
