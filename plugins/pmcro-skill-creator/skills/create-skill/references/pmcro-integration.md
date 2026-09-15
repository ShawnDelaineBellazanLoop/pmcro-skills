# PMCRO integration

Use PMCRO as an explicit lifecycle contract around skill creation, not as a replacement for validation or tool permissions.

## Phase contracts

- **Planner:** produce minimal acceptance-testable steps.
- **Maker:** create complete files and scripts; never silently stub.
- **Checker:** independently inspect files, manifests, links, hashes, and runtime results.
- **Reflector:** convert evidence and failures into concise reusable constraints.
- **Orchestrator:** choose `ACCEPT`, `EXTEND`, `LOOP`, `ESCALATE`, or `INTERRUPT` under bounded limits.

All phase messages should use typed JSON envelopes. Persist evidence, tool calls, timestamps, hashes, verdicts, and constraints. Do not persist hidden chain-of-thought as the audit record.

## Forward-only rule

Maker and Checker do not directly call Planner or Maker again. Their outcomes flow to Reflector, then Orchestrator opens a new cycle if required. This prevents unbounded regression loops.

## Anthropic and MAF mapping

- Progressive disclosure maps to advertise → load → read resources → run scripts.
- Tool use maps to explicit script calls with approval for side effects.
- Structured output maps to envelope schemas and machine-checkable verdicts.
- Context discipline maps to short `SKILL.md` plus on-demand references.
- Ground truth maps to Checker evidence rather than agent self-report.

The repository-level implementation is in `.pmcro/`; use its laws, schemas, templates, and scripts rather than recreating them in each skill.
