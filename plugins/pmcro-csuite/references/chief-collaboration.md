# Chief collaboration

Each Chief is a bounded domain lead. A Chief may contain internal specialist roles, but specialists do not receive operational tools by default.

```text
Chief proposal or DomainRequest
    ↓
PMCRO Orchestrator validates and routes
    ↓
Target Chief produces a typed result
    ↓
Orchestrator records a TrailFrame
    ↓
Source Chief receives a PhaseMessage referencing that frame
```

## Research dependency example

```text
CTO needs technical fact
→ CTO emits ResearchRequest
→ Orchestrator routes to CKO
→ CKO uses approved research tools
→ CKO emits ResearchFrame with sources and confidence
→ Orchestrator records and delivers frame
→ CTO reads frame and emits TechnicalRecommendation
```

A dependent Chief must not treat missing research as complete. It must wait, mark the recommendation provisional, or escalate.

Chief recommendations are proposals, not acceptance evidence. Checker evidence remains the acceptance gate. Tool execution remains Orchestrator-only.
