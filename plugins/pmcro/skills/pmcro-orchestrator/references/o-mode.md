# O-Mode

O-Mode is the bounded Orchestrator mode for turning an ambiguous seed into a validated IntentEnvelope and a minimal PlanEnvelope before the PMCRO cycle runs.

## Stages

1. **Receive:** preserve the raw seed without treating every phrase as a requirement.
2. **Normalize:** state the surface intent in plain language.
3. **Excavate:** form a confidence-rated truest-intent hypothesis.
4. **Ground:** load laws, constraints, high-level goals, Trail state, and validated resources.
5. **Classify:** separate required, desired, speculative, blocked, and out-of-scope items.
6. **Select:** choose the least-complex strategy family that can satisfy acceptance criteria.
7. **Plan:** emit a minimum PlanEnvelope with observable acceptance criteria.
8. **Dispatch:** route through Planner, Maker, Checker, and Reflector.
9. **Decide:** emit one bounded OrchestratorDecision.

## Contract

O-Mode output must contain `surface_intent`, `truest_intent`, `confidence`, classifications, `strategy_id`, `selection_reason`, a PlanEnvelope, evidence references, and approval requirements. `truest_intent` is a hypothesis, not a claim of mind-reading.

## Guardrails

- Do not invent missing requirements.
- Do not use unvalidated URLs or assets as authoritative planning inputs.
- Do not silently broaden scope.
- Do not bypass Checker or approval gates.
- Do not store private chain-of-thought; store decisions, summaries, tools, scores, and evidence.
- If confidence is low and the ambiguity changes scope or safety, emit `ESCALATE` or request clarification.

O-Mode is runtime behavior owned by `pmcro-skill-creator`. The `skill-creator` plugin may scaffold O-Mode-compatible packages but does not execute the lifecycle.
