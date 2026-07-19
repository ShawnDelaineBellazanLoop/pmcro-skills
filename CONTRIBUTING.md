# Contributing to pmcro-skills

`pmcro-skills` is a standalone skill catalog for the PMCR-O Colony, built to a convention
similar to [managedcode/dotnet-skills](https://github.com/managedcode/dotnet-skills) —
each skill is a self-contained package with a `manifest.json`, a `SKILL.md`, and a
`references/` folder, indexed centrally in `catalog/skills.json`. (This link was a bare,
unresolved placeholder before; verified by web search, not confirmed as the original
source.)

## Adding a New Skill

1. Pick the correct **lane** (`Tools`, `Frameworks`, `Libraries`, `Platform`, `Testing`) and
   create the folder:

   ```text
   catalog/<Lane>/<Category>/skills/<skill-name>/
   ├── manifest.json
   ├── SKILL.md
   ├── scripts/       (only if the skill has an executable payload)
   ├── references/    (supporting docs the agent reads, not executes)
   └── assets/         (templates/static files scripts consume)
   ```

   `scripts/`, `references/`, and `assets/` are the *only* subfolders MAF's
   `AgentSkillsProvider` recognizes — do not invent new ones (e.g. `templates/`, `schemas/`).

2. Write `manifest.json`:

   ```json
   { "version": "1.0.0", "category": "<category>", "packages": ["<PackageName>"] }
   ```

3. Write `SKILL.md` with YAML frontmatter (`name`, `description`, `compatibility`) followed
   by these required sections, in order:

   - `Trigger On`
   - `Value`
   - `Do Not Use For`
   - `Inputs`
   - `Quick Start`
   - `Workflow`
   - `Bootstrap When Missing` (if applicable)
   - `Deliver`
   - `Validate`
   - `Ralph Loop` — the skill's own internal plan → execute → review → fix cycle
   - `Required Result Format` (`status` / `plan` / `actions_taken` / `validation_skills` /
     `verification` / `remaining`)
   - `Load References`
   - `Example Requests`

   The `description` field must follow the `USE FOR: ... DO NOT USE FOR: ... INVOKES: ...`
   pattern — this is what downstream orchestration uses to route work to the right skill.

4. Add an entry to `catalog/skills.json` matching `catalog/skills.schema.json`. `path` must
   end in `/` and point at the skill folder itself (not the category folder).

5. Run the validator locally before opening a PR:

   ```bash
   pip install -r scripts/requirements.txt
   python3 scripts/validate_catalog.py
   ```

## Naming Discipline

The five PMCR-O roles (Orchestrator, Planner, Maker, Checker, Reflector) are **not** skills
and must never be packaged here — they are the Colony's compiled runtime, not MAF-loadable
capabilities. If you're unsure whether something belongs in this repo vs. `.pmcro/agents/`
in the consuming project, it belongs here only if MAF's `AgentSkillsProvider` should be able
to discover and invoke it as a standalone capability.

## Review

Every PR runs `Catalog CI` (schema validation, frontmatter lint, markdownlint). All checks
must pass before merge.
