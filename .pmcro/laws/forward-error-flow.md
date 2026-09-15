# Forward error flow

Every phase outcome flows through the PMCRO lifecycle, including errors.

```text
Planner → Maker → Checker → Reflector → Orchestrator
```

A Checker failure does not call Maker directly. Checker emits evidence-backed failure data. Reflector converts it into a new `SeedIntent`, constraints, and a strategy hint. Orchestrator decides whether to open a bounded new cycle, extend scope, escalate, interrupt, or accept.

Errors are data, not permission to retry forever. Apply cycle, attempt, time, output, and approval limits. Persist the failure, evidence, reflection, seed, and decision as TrailFrames.
