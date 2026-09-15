# Strategy selection

Reasoning strategy families are execution policies, not hidden-thought formats. Select the least complex family that can satisfy the plan and produce independent evidence.

## Families

- `plan-execute-verify`: default for linear tasks.
- `react`: iterative tool use in a changing environment.
- `decomposition`: independent subproblems that can be aggregated.
- `dependency-graph`: ordered work with prerequisites.
- `branch-select`: bounded alternatives scored against criteria.
- `debate-referee`: independent proposals for high-impact decisions.
- `retrieve-ground`: source-backed work where repository or external facts matter.
- `refine-check`: measurable repair of an existing artifact.

Record `strategy_id`, `selection_reason`, `model_family`, tool calls, outputs, scores, and evidence references. Never record or require private chain-of-thought.

## Model-family guidance

Model families are capabilities, not vendor identities. Route by measured behavior:

- Tool-calling family: external operations and structured function calls.
- Code family: implementation, parsing, and test repair.
- Long-context family: large reference comparison, with retrieval limits.
- Vision/multimodal family: image or UI evidence.
- Fast/low-cost family: classification, extraction, and simple checks.
- Deliberative family: bounded alternative analysis and high-impact review.

Do not assume a model is suitable from its name. Maintain a capability profile with tool-call reliability, structured-output reliability, context capacity, latency, cost, and known failure modes. The Orchestrator may select a model family, but the Checker decides whether the resulting artifact is correct.
