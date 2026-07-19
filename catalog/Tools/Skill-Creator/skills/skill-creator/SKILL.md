---
name: skill-creator
description: "Create, update, validate, and publish MAF Agent Skills for the pmcro-skills catalog. USE FOR: authoring a new skill package (manifest.json + SKILL.md + scripts/references/assets); updating an existing skill's frontmatter, workflow, or references; validating a skill against catalog/skills.schema.json before it's added to catalog/skills.json; deciding whether new capability belongs in catalog/ (a skill) vs the consuming project's .pmcro/ (runtime policy/state) vs this repo's agents/ (one of the five fixed PMCR-O roles, or a package/skill-scoped router). DO NOT USE FOR: implementing the actual PMCR-O runtime (Orchestrator/Planner/Maker/Checker/Reflector) — those are AGENT.md role definitions under this repo's agents/, never skill packages. DO NOT USE FOR: executing a skill's own scripts — that's run_skill_script's job at runtime, not this skill's. INVOKES: interview the requester on skill scope, draft SKILL.md + manifest.json from templates in assets/, validate against schema, update catalog/skills.json, report status."
compatibility: "Targets Microsoft Agent Framework's AgentSkillsProvider (file-based skills). Requires Python 3.12+ and jsonschema to run scripts/validate_skill.py locally."
---

# Skill Creator

## Trigger On

- "create a skill for X" / "add a skill to the catalog" / "package this as a skill"
- "update the `<name>` skill" / "fix this skill's frontmatter"
- "is this skill catalog-ready?" / "validate this skill"
- Any question about whether something belongs in `catalog/` (a skill) vs `agents/`
  (orchestration) vs a consuming project's `.pmcro/` (runtime state)

## Value

- Every skill in `pmcro-skills` looks and behaves the same way, regardless of who wrote it
  or how long ago — MAF's `AgentSkillsProvider` and the Colony's own tooling can rely on a
  single, predictable shape.
- Reduces ambiguity between "this is a skill" and "this is runtime policy" — a distinction
  that has been gotten wrong before in this project's history and is expensive to unwind.
- Produces a concrete artifact (a validated skill package) plus verification evidence
  (`validate_catalog.py` output), not just advice.

## Do Not Use For

- Writing the actual runtime that loads and executes skills — that's MAF's
  `AgentSkillsProvider` (already built, not this skill's job).
- Representing the Orchestrator, Planner, Maker, Checker, or Reflector as a skill package.
  These are the PMCR-O runtime itself, defined under this repo's `agents/`. See
  `references/pmcro-conventions.md`.
- Business-process definitions ("trails") — those live under a consuming project's
  `.pmcro/trails/`, not here.

## Inputs

- What capability/tool does the skill wrap? (e.g. git, docker, a specific CLI)
- Is this new, or updating an existing catalog entry?
- Does it need `scripts/` (executable), `references/` (docs), `assets/` (templates/static
  files), or some combination? At least one of the three, or the skill is just metadata.
- Which lane: `Tools`, `Frameworks`, `Libraries`, `Platform`, or `Testing`?

## Quick Start

1. Read `references/skill-anatomy.md` to confirm the target shape.
2. Read `references/pmcro-conventions.md` to confirm the thing being built is actually a
   skill, not runtime policy in disguise.
3. Copy `assets/SKILL.template.md` and `assets/manifest.template.json` into the new skill
   folder and fill them in.
4. Add the entry to `catalog/skills.json`.
5. Run `python3 scripts/validate_skill.py <skill-path>` (or the repo-root
   `scripts/validate_catalog.py` for the whole catalog).

## Workflow

This skill follows the PMCR-O lifecycle rather than a generic authoring loop — it's a
Colony skill, so it behaves like one:

1. **Observe** — detect the need. A new capability is required, or an existing skill's
   frontmatter/behavior has drifted from what it actually does.
2. **Plan** — determine skill boundaries: name, lane, category, whether it needs
   `scripts/`/`references/`/`assets/`, and what its `USE FOR / DO NOT USE FOR / INVOKES`
   description must say to trigger correctly and not overtrigger.
3. **Create** — generate the package from `assets/` templates. Write real content, not
   placeholder text — an unfilled `<placeholder>` in output is a hard fail (see `PLAN-001`
   in `references/pmcro-conventions.md`).
4. **Check** — validate against `catalog/skills.schema.json` and confirm `SKILL.md`
   frontmatter (`name`, `description`) matches the `catalog/skills.json` entry exactly.
5. **Reflect** — if validation fails, diagnose why (see `Required Result Format` below) and
   fix in the next iteration. Do not loop more than 3 times without surfacing the blocker.
6. **Publish** — add/update the `catalog/skills.json` entry.
7. **Exercise** — recommend a first real invocation to confirm the skill actually triggers
   and behaves as described (not just schema-valid).
8. **Learn** — if the skill needed a correction after use, capture it as a note in the
   skill's own `references/` so the next author doesn't repeat the mistake.

## Bootstrap When Missing

If this is the very first skill in a new lane/category:

1. Confirm the lane exists under `catalog/` (`Tools`, `Frameworks`, `Libraries`, `Platform`,
   `Testing`) — create it if not.
2. Create `catalog/<Lane>/<Category>/skills/<skill-name>/` with `manifest.json`, `SKILL.md`,
   and whichever of `scripts/`, `references/`, `assets/` the skill actually needs. Do not
   create empty subfolders "just in case" — MAF only advertises `read_skill_resource` when
   resources exist and `run_skill_script` when scripts exist, so unused folders add nothing.

## Deliver

- A skill folder matching `references/skill-anatomy.md`
- A `catalog/skills.json` entry that validates against `catalog/skills.schema.json`
- A one-line status report: what was created/changed, what still needs a human decision

## Validate

- `SKILL.md` frontmatter `name` matches the folder name and the catalog entry exactly
- `description` follows `USE FOR / DO NOT USE FOR / INVOKES`
- No PMCR-O role name (Orchestrator/Planner/Maker/Checker/Reflector) used as a skill name
- No `pmcro-` prefix on the skill name — see naming discipline in
  `references/pmcro-conventions.md`
- No placeholder text (`<...>`, `{...}`, `TODO`) left in delivered files

## Required Result Format

- `status`: `created` | `updated` | `validated` | `blocked`
- `skill_path`: the catalog path written or checked
- `actions_taken`: concrete files created/edited
- `validation_result`: pass/fail per `scripts/validate_skill.py`, with specific failures if any
- `remaining`: open decisions that need a human call, or `none`

## Load References

- [references/maf-agent-skills.md](references/maf-agent-skills.md) — how MAF's
  `AgentSkillsProvider` actually discovers, advertises, and executes skills
- [references/pmcro-conventions.md](references/pmcro-conventions.md) — what is/isn't a
  skill in this Colony, and the naming discipline decision
- [references/skill-anatomy.md](references/skill-anatomy.md) — the exact folder/file shape,
  including where `agents/` fits at repo-root, package, and skill-scoped levels
- [references/ralph-loop.md](references/ralph-loop.md) — one authoring methodology this
  skill can apply during the Create step; not the central concept, just a reference

## Example Requests

- "Create a git skill for local version control, Tools lane."
- "Update the docker skill's description, it's not triggering on 'container' phrasing."
- "Is `powershell` still catalog-compliant, or does it need the schema upgrade too?"
- "Validate the whole catalog before I open a PR."
