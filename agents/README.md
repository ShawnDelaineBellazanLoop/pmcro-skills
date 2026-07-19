# PMCR-O Orchestration Agents

This repository maintains two parallel content layers, same convention as
[dotnet-agent-skills](https://github.com/managedcode/dotnet-skills):

- [`catalog/`](../catalog): narrow, reusable capability packages (`SKILL.md`) — what an
  agent knows how to do
- `agents/` (this folder): broad orchestration agents that own the PMCR-O cycle and
  route into the right skills — how an agent decides what to do next

## Roles

- [`orchestrator/AGENT.md`](orchestrator/AGENT.md) — owns the high-level goal, O-Mode,
  dispatch order, and SeedIntentFrame emission
- [`planner/AGENT.md`](planner/AGENT.md) — turns a dispatched Trail into
  execution_plan_json
- [`maker/AGENT.md`](maker/AGENT.md) — executes the plan, invokes catalog skills,
  produces evidence
- [`checker/AGENT.md`](checker/AGENT.md) — scores Maker's output, issues PASS/LOOP
- [`reflector/AGENT.md`](reflector/AGENT.md) — diagnoses a LOOP verdict, produces
  EarnedConstraints

See [`registry.md`](registry.md) for the full role/file/law index — the single source
of truth read by the Orchestrator (and by any human or session picking up an
interrupted Trail).

## Layout

```text
agents/
├── README.md
├── registry.md
└── <role>/
    ├── AGENT.md
    ├── scripts/       # optional — none of the five roles need this today
    ├── references/    # optional
    └── assets/        # optional
```

Same optional `scripts/`/`references/`/`assets/` convention as `catalog/` skill
packages — see `catalog/Tools/Skill-Creator/skills/skill-creator/references/
skill-anatomy.md`.

## What Does Not Live Here

- Capability packages (docker, filesystem, playwright, git, etc.) — those are `catalog/`
  skills, discovered by MAF's `AgentSkillsProvider`, not referenced by name here.
- Trails (business-process definitions that compose skills) and other runtime state
  (frames, memory, knowledge) — those are project-specific and live under the
  consuming project's `.pmcro/`, not in this catalog repo.

## Consumption

These five `AGENT.md` files are the canonical source. A consuming project (e.g.
`ProjectName`) pulls a copy into its own tree rather than editing them here directly —
see the open decision on the copy/sync mechanism in `catalog/Tools/Skill-Creator/skills/
skill-creator/references/pmcro-conventions.md`.
