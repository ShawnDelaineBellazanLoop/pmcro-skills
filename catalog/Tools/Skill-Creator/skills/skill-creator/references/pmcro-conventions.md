# PMCR-O Conventions for Skill Authoring

These are locked architecture decisions from prior sessions, restated here so
`skill-creator` doesn't have to re-litigate them every time it's invoked.

## What Is a Skill vs. What Is Runtime

```
Microsoft Agent Framework
        │
        ▼
    Agent Runtime
        │
        ▼
    PMCR-O Runtime            ← agents/<role>/AGENT.md, this repo's root
        ├── Orchestrator / O-Mode
        ├── Planner
        ├── Maker
        ├── Checker
        ├── Reflector
        │
        ▼
      Agent Skills            ← catalog/, this repo
        │
        ▼
Filesystem • Docker • Git • Playwright • MCP • ...

(Constraints, Laws, Memory, Knowledge, Frames, Trails, Evidence are project-specific
 runtime STATE — they live in the consuming project's `.pmcro/`, not in this repo.)
```

- **The five PMCR-O roles are the runtime, not skills.** Orchestrator, Planner, Maker,
  Checker, Reflector are `AGENT.md` role definitions (potentially backed by compiled C#
  services). They are never packaged as `SKILL.md` capability packages. This was gotten
  wrong once already and cost a rebuild — don't repeat it.
- **Canonical source for the five roles is this repo's top-level `agents/`, not the
  consuming project's `.pmcro/`.** Verified against the actual `dotnet-agent-skills`
  repo on disk (not assumed): it maintains a top-level `agents/<agent>/AGENT.md` layer,
  sibling to `catalog/`, for "broader orchestration agents that triage work and route
  into the right skills" — distinct from package-scoped `catalog/<lane>/<package>/
  agents/<agent>/AGENT.md` (routes across one package's skills) and skill-scoped
  `catalog/<lane>/<package>/skills/<skill>/agents/<agent>/AGENT.md` (travels with one
  skill only). PMCR-O's five roles are the first kind — broad orchestration above the
  whole catalog — so they live in `agents/<role>/AGENT.md` at this repo's root. See
  `agents/README.md` and `agents/registry.md`. A consuming project pulls a copy rather
  than hand-authoring its own; the copy/sync mechanism is still an open decision (same
  open item as the skills-side consumption question).
- **Constraints, Laws, Memory, Knowledge, Evidence, Trails are runtime state/policy,
  not skills, and are NOT portable the way the five roles are.** They live under the
  consuming project's `.pmcro/` (e.g. `.pmcro/laws/`, `.pmcro/trails/`, `.pmcro/memory/`),
  not in this catalog repo and not under `.agents/skills/`. Unlike the five roles, this
  state is inherently project-specific (a Trail belongs to one project's business
  process) and has no canonical-source-repo equivalent.
- **Skills answer "how do I perform this capability?"** Runtime answers "what should I
  do next, why, and under what constraints?" If what you're building answers the second
  question, it's an `agents/` entry (or project-side `.pmcro/` state), not a `catalog/`
  skill.
- **Trails are the product; skills are what trails consume.** A trail is a business
  process (`.pmcro/trails/onboarding/`, `.pmcro/trails/architecture-review/`) that
  references one or more skills. Don't confuse the two.

## Naming Discipline

- **No `pmcro-` prefix on skill names.** A skill's name describes what it does
  (`git`, `docker`, `filesystem`), not which framework or colony it belongs to.
  `dotnet-agent-skills` doesn't prefix `csharpier` as `dotnet-csharpier` — the framework
  identity lives in `category`/`lane`/`compatibility` metadata, not the name.
- **This is why the meta-skill is `skill-creator`, not `pmcro-skill-creator`.** PMCR-O's
  opinions live inside its `references/` and `SKILL.md` body, not its identity — that
  keeps it portable if it's ever reused outside this Colony.
- **No PMCR-O role names as skill names**, ever, for the same reason roles aren't
  packaged as skills at all.

## Agent Definitions Stay Thin

`agents/<role>/AGENT.md` files (this repo's root — see above) declare role, delegation,
and routing — they do not restate how PMCR-O works internally. Real shape, verified
against the migrated role files:

```yaml
---
name: maker
description: "Executes the approved plan and produces real, verifiable output. Use
  after the Planner has produced execution_plan_json..."
skills:
  - docker
  - filesystem
  - playwright
  - git
---
## Role
...
## Owns
...
## Does Not Own
...
## Invariant Enforcement
...
```

`tools:`/`model:` fields (seen in `dotnet-agent-skills`' own `AGENT.md` files, which
target Claude Code subagents specifically) are omitted here — the five PMCR-O roles
target MAF's agent runtime generically, not one specific coding-agent product, so those
fields don't apply unless a specific consuming project's build needs them.

The runtime's actual reasoning policy (O-Mode, frame generation, reflection loops) is
documented in each role's own `AGENT.md` body and implemented in code / the consuming
project's `.pmcro/`, not restated across every file.

## Hard Constraints

- `PLAN-001` — No placeholder parameters (`<...>`, `{...}`, `TODO`) in delivered output.
  A skill package with unfilled template text fails validation.
- `EC-004` — The authoring agent (Maker-equivalent) does not self-score its own output;
  `scripts/validate_skill.py` / `validate_catalog.py` is the Checker step, run
  separately.
- `EC-009` — Don't loop authoring/validation more than 3 times without surfacing the
  blocker to a human. Runaway self-correction is a failure mode, not diligence.
