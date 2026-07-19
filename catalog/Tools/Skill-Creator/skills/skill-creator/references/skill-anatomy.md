# Skill Anatomy — Exact Shape

```
catalog/<Lane>/<Category>/skills/<skill-name>/
├── manifest.json      # required
├── SKILL.md           # required
├── scripts/           # optional — only if MAF's run_skill_script should be advertised
├── references/        # optional — only if MAF's read_skill_resource should be advertised
└── assets/             # optional — templates/static files scripts or output consume
```

`scripts/`, `references/`, and `assets/` are the **only** subfolders MAF's file-based skill
source recognizes. Do not invent new ones (`templates/`, `schemas/`, `docs/`) at the skill
root — put that content inside `references/` or `assets/` instead.

## `manifest.json`

```json
{ "version": "1.0.0", "category": "<category>", "packages": ["<PackageName-or-empty>"] }
```

## `SKILL.md` Frontmatter

```yaml
---
name: <kebab-case, matches folder name and catalog.json entry exactly>
description: "USE FOR: ... DO NOT USE FOR: ... INVOKES: ..."
compatibility: "<what this skill requires to function>"
---
```

## `SKILL.md` Body — Required Sections, In Order

1. `Trigger On`
2. `Value`
3. `Do Not Use For`
4. `Inputs`
5. `Quick Start`
6. `Workflow`
7. `Bootstrap When Missing` (if the skill has a "not configured yet" state)
8. `Deliver`
9. `Validate`
10. `Ralph Loop` or equivalent internal plan→execute→review→fix cycle (see
    `ralph-loop.md` — optional citation, but *some* internal iteration loop is required)
11. `Required Result Format`
12. `Load References`
13. `Example Requests`

## `catalog/skills.json` Entry

Must validate against `catalog/skills.schema.json`. Minimum required fields: `name`,
`title`, `version`, `category`, `type`, `package`, `lane`, `description`, `compatibility`,
`path`, `tokenCount`. `path` must end in `/` and point at the skill folder itself.

## Size Discipline

Keep `SKILL.md` under ~500 lines — it loads into context on every trigger (see
`maf-agent-skills.md` → Four-Stage Progressive Disclosure). If a skill needs more than
that, split domain-specific detail into `references/<domain>.md` files and point to them
from `SKILL.md` rather than inlining everything.

## `agents/` Is a Sibling Structure, Not a Skill Subfolder

`agents/` never appears *inside* a skill folder's own required set above. It exists at
three possible levels, verified against the real `dotnet-agent-skills` repo on disk:

```
agents/<role>/AGENT.md                                          ← repo root (this repo)
catalog/<Lane>/<Category>/agents/<agent>/AGENT.md                ← package-level
catalog/<Lane>/<Category>/skills/<skill>/agents/<agent>/AGENT.md ← skill-scoped
```

- **Repo-root `agents/`** — broad orchestration that sits above the whole catalog. This
  is where PMCR-O's five roles (Orchestrator, Planner, Maker, Checker, Reflector) live.
  See `pmcro-conventions.md`.
- **Package-level `agents/`** (sibling to that package's own `skills/`) — routes across
  multiple skills *within one package* (e.g. a hypothetical router across several
  version-control-adjacent skills in `Tools/Git`). Optional; most packages don't have
  one.
- **Skill-scoped `agents/`** (nested inside one specific skill folder) — a specialist
  that only makes sense next to that one skill.

Each `<agent>/` folder follows the same optional-subfolder convention as a skill:
`AGENT.md` required, `scripts/`/`references/`/`assets/` optional. `skill-creator` does
not currently author `agents/` packages — see `Do Not Use For` in its own `SKILL.md` —
but should recognize this shape when validating or discussing where new capability
belongs.
