---
name: pmcro-orchestrator
description: "Orchestrate bounded Planner-Maker-Checker-Reflector-Orchestrator cycles using O-Mode, typed envelopes, selectable reasoning strategy families, independent evidence checks, approval gates, and append-only Trails. Use for multi-step work requiring phase separation and controlled iteration; do not use for simple one-step tasks."
license: MIT
compatibility: "MAF-compatible skill package. Requires a host adapter to instantiate agents and a trusted script runner for local control scripts."
metadata:
  version: "0.1.0"
  protocol: pmcro
  tools: orchestrator-only
---

# Purpose

Coordinate a forward-only PMCRO cycle while keeping context lean, state typed, strategy selection explicit, and completion evidence-based.

## Workflow

1. Run [O-Mode](references/o-mode.md) on the messy seed.
2. Load `.pmcro` laws, constraints, Trail state, high-level goal, and validated resources.
3. Load [agent registry](assets/agents-index.json) and validate paths.
4. Select the least-complex strategy from [strategy catalog](assets/strategy-catalog.json), or use `o-mode` when refinement is required.
5. Resolve the current phase and load only that phase skill.
6. Dispatch typed PhaseMessages through the [runtime boundary](references/runtime-boundary.md); never use slash-command text as the inter-agent protocol.
7. Run `Planner → Maker → Checker → Reflector → Orchestrator`; failures flow forward.
8. Require independent Checker evidence before `ACCEPT`.
9. Record strategy, model family, tool calls, outputs, hashes, verdict, and constraints in the Trail.
10. Apply cycle, time, output, and approval limits from `.pmcro` configuration.

## Authority boundary

Phase agents and Chiefs return structured plans, ToolIntents, DomainRequests, and results; they do not call tools. Only this Orchestrator executes MAF script tools, MCP tools, CodeAct, queue adapters, webhook handlers, or filesystem operations, subject to approval policy.

## Contracts

Use `.pmcro/schemas/` for IntentEnvelope, PlanEnvelope, ArtifactEnvelope, CheckReport, ReflectionFrame, OrchestratorDecision, TrailEvent, PhaseMessage, TrailFrame, and DomainRequest. Planner must complete seed-to-true-intent extraction before producing a PlanEnvelope.

## Validation

Accept only when acceptance criteria pass, required evidence exists, no unsafe path or unapproved side effect occurred, and the Orchestrator emits `ACCEPT`. Otherwise emit `EXTEND`, `LOOP`, `ESCALATE`, or `INTERRUPT`.

## Resources

- [O-Mode](references/o-mode.md)
- [Phase responsibilities](references/phase-responsibilities.md)
- [Message versus Trail Frame](references/message-vs-frame.md)
- [Runtime boundary: dispatch, queue, ingress, host preflight](references/runtime-boundary.md)
- [MAF agent loading](references/maf-agent-loading.md)
- [Strategy selection](references/strategy-selection.md)
- [Agents index](assets/agents-index.json)
- [Strategy catalog](assets/strategy-catalog.json)
- [O-Mode result schema](assets/o-mode-result.schema.json)
