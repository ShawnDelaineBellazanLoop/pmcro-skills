---
name: plugin-packager
description: "USE FOR: converting an existing PMCR-O catalog skill (manifest.json + SKILL.md, dotnet-agent-skills convention, under catalog/<lane>/<package>/skills/<skill>/) into a Cowork/Claude Code-compatible .plugin package (.claude-plugin/plugin.json + skills/<skill>/SKILL.md); answering whether a given catalog skill is plugin-compatible. DO NOT USE FOR: authoring a brand-new skill from scratch — that's skill-creator's job. DO NOT USE FOR: packaging the PMCR-O orchestrator/loop itself — it's a hosted C# runtime, not a skill, and cannot be exported as a plugin. INVOKES: read the source manifest.json + SKILL.md, map fields into plugin.json, reconcile SKILL.md frontmatter, copy scripts/references/assets unchanged, zip as .plugin, present to requester."
compatibility: "Requires Python 3.12+ and the zip utility. Reads from an existing catalog/<lane>/<package>/skills/<skill>/ directory — does not create skill content, only repackages it."
---

# Plugin Packager

## Trigger On

- "package/export/wrap [skill] as a plugin"
- "is [skill] plugin-compatible" / "can I load this in Cowork"
- "make a plugin out of the catalog skill for X"

Bridges two skill conventions that already coexist in the PMCR-O project:

| | PMCR-O catalog skill | Cowork / Claude Code plugin |
|---|---|---|
| Manifest | `manifest.json` (dotnet-agent-skills) | `.claude-plugin/plugin.json` |
| Instructions | `SKILL.md` | `skills/<skill-name>/SKILL.md` |
| Consumer | MAF's `AgentSkillsProvider` | Claude Cowork / Claude Code |
| Extras | `scripts/`, `references/`, `assets/` | same, unchanged |

They already share the same three-tier shape (metadata → body → bundled resources), so this is a **structural repackage**, not a rewrite. Never re-author the skill's actual instructions — carry the body across untouched unless the user asks for changes.

## When NOT to use this

- Building a new skill from nothing → use `skill-creator` instead.
- The user names a specific catalog skill that doesn't exist yet → confirm the source path first; don't invent content.
- The target is the full PMCR-O orchestrator/loop, not a single skill → that's a hosted system, not a plugin. Say so plainly rather than trying to force it into plugin shape (see prior conversation: only the skill layer ports, the Colony runtime does not).

## Workflow

### 1. Locate the source skill

Expect a path like `pmcro-skills/catalog/<lane>/<package>/skills/<skill>/`. It should contain:
- `manifest.json`
- `SKILL.md`
- optionally `scripts/`, `references/`, `assets/`

If the user only names the skill (not the path), search the catalog for a matching folder before asking them to locate it manually.

Read both `manifest.json` and `SKILL.md` before doing anything else — the manifest usually carries fields (version, author, dependencies) that the plugin manifest also needs, and that aren't in the SKILL.md frontmatter.

### 2. Map manifest.json → plugin.json

`manifest.json` (dotnet-agent-skills) typically has fields like `name`, `version`, `description`, `author`, `dependencies`. Map to:

```json
{
  "name": "<kebab-case-name>",
  "version": "<semver, default 0.1.0 if absent>",
  "description": "<from manifest or SKILL.md frontmatter>",
  "author": { "name": "<from manifest, else omit>" }
}
```

Enforce plugin.json's stricter naming rule: `name` must be kebab-case, lowercase, hyphens only — sanitize if the source uses underscores or PascalCase.

### 3. Build the plugin directory

```
<skill-name>/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md          (copied from source, frontmatter reconciled — see step 4)
│       ├── scripts/           (copied as-is, if present)
│       ├── references/        (copied as-is, if present)
│       └── assets/            (copied as-is, if present)
└── README.md                  (brief: what this plugin does, and that it was exported from pmcro-skills catalog)
```

### 4. Reconcile SKILL.md frontmatter

The source SKILL.md frontmatter may include PMCR-O-specific fields (`Role`, `Owns`, `Does Not Own`, or dotnet-agent-skills fields like `tools`, `model`, `skills`). Cowork's SKILL.md frontmatter only recognizes `name` and `description` (`compatibility` is optional). Keep the extra PMCR-O fields out of the emitted frontmatter — they're meaningless to Cowork's loader — but you may fold relevant context into the body text if it helps a reader unfamiliar with the source system understand scope.

Don't touch the instructional body itself beyond that. This isn't a rewrite step.

### 5. Validate structure manually

(No `claude plugin validate` CLI available in this environment — check by hand.)

- `.claude-plugin/plugin.json` exists, valid JSON, has `name`
- `name` is kebab-case
- `skills/<name>/SKILL.md` exists
- Any referenced `scripts/`/`references/`/`assets/` directories that exist actually contain files

### 6. Package

```bash
cd /path/to/<skill-name> && zip -r /tmp/<skill-name>.plugin . -x "*.DS_Store" && cp /tmp/<skill-name>.plugin /path/to/outputs/<skill-name>.plugin
```

Always stage the zip in `/tmp/` first, then copy to the outputs directory.

### 7. Present

Use `present_files` to hand back the `.plugin` file. Briefly note which source catalog skill it was exported from and confirm nothing in the instructional body was altered (or list what was, if the user asked for changes).

## Batch mode

If the user wants several catalog skills packaged at once (e.g., "package git and skill-creator"), repeat steps 1–6 per skill and present all resulting `.plugin` files together — don't bundle multiple unrelated skills into a single plugin unless the user explicitly asks for a combined plugin.

## Reference

- `references/format-comparison.md` — full field-by-field comparison between dotnet-agent-skills manifest.json and Cowork's plugin.json/SKILL.md frontmatter, for edge cases not covered above.
