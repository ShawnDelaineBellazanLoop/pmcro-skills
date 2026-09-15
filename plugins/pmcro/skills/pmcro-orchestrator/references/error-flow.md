# Orchestrator error flow

Treat every result as a PMCRO outcome. When Checker reports an error:

1. Preserve CheckReport and evidence.
2. Route it to Reflector.
3. Require Reflector to emit a SeedIntent and constraints.
4. Run O-Mode on the new seed.
5. Select a bounded next strategy or escalate.
6. Open a new cycle only within configured limits.

Never call Maker directly from Checker. Never treat an error as permission for unlimited retries.
