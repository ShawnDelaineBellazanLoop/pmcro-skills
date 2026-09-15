# PhaseMessage, TrailFrame, and Trail

A `PhaseMessage` transports work between phases or domain teams. It is short-lived, idempotent, and references payloads or durable frames.

A `TrailFrame` is durable verified state from a meaningful phase result. It contains a summary, evidence references, provenance, confidence, hashes, and timestamp.

The Trail is the ordered record of frames, with low-level events and indexes around them:

```text
PhaseMessage → TrailEvent → TrailFrame → Trail
```

Messages do not become authoritative merely because they were delivered. A frame becomes usable as evidence only after the responsible Checker or resource validator marks it verified.

Chiefs and phase agents communicate through typed messages routed by the Orchestrator. They do not call one another directly and do not use slash-command text as a protocol.
