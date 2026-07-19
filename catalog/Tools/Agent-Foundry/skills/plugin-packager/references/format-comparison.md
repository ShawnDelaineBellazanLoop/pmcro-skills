# Format Comparison: dotnet-agent-skills vs Cowork Plugin

## manifest.json (dotnet-agent-skills / PMCR-O catalog) — typical fields

```json
{
  "name": "git",
  "version": "1.0.0",
  "description": "Git operations for the PMCR-O colony.",
  "author": "PMCR-O AI Agent Company",
  "tools": ["Bash", "Read", "Write"],
  "model": "inherit",
  "skills": ["git-local"],
  "dependencies": []
}
```

## plugin.json (Cowork / Claude Code) — required + optional fields

```json
{
  "name": "git",
  "version": "1.0.0",
  "description": "Git operations for the PMCR-O colony.",
  "author": { "name": "PMCR-O AI Agent Company" },
  "homepage": "",
  "repository": "",
  "license": "",
  "keywords": []
}
```

## Field-by-field mapping

| manifest.json field | plugin.json field | Notes |
|---|---|---|
| `name` | `name` | Sanitize to kebab-case if not already |
| `version` | `version` | Same semver format, carry over directly |
| `description` | `description` | Carry over; may also appear in SKILL.md frontmatter |
| `author` (string) | `author.name` | Wrap bare string in `{ "name": ... }` object |
| `tools` | *(no direct equivalent)* | Cowork doesn't gate tool access at the manifest level — drop, or mention in README if relevant context |
| `model` | *(no equivalent)* | PMCR-O-specific (MAF model routing) — drop |
| `skills` (sub-skill list) | *(implicit via directory)* | Cowork discovers skills by directory presence under `skills/`, not by manifest listing — no field needed |
| `dependencies` | *(no equivalent)* | If these are other PMCR-O skills, note in README that the plugin assumes standalone use — Cowork plugins don't have a native dependency resolution mechanism |

## SKILL.md frontmatter differences

**PMCR-O catalog SKILL.md** may include:
```yaml
---
name: git
description: ...
Role: specialist
Owns: git operations
Does Not Own: deployment
tools: [Bash]
model: inherit
---
```

**Cowork SKILL.md** recognizes only:
```yaml
---
name: git
description: ...
compatibility: (optional — required tools/environment note, plain text)
---
```

Drop `Role`, `Owns`, `Does Not Own`, `tools`, `model`, `skills` from the emitted frontmatter. If any of that context is useful for a human reader, fold it into the body prose rather than the frontmatter — Cowork's loader ignores unrecognized frontmatter keys, but keeping them out avoids confusion for anyone editing the plugin later.

## What carries over untouched

- The instructional body of SKILL.md (the actual how-to content)
- `scripts/` — executable helpers, no format changes needed
- `references/` — loaded on demand the same way in both systems
- `assets/` — templates/icons/fonts, no changes

## What has no equivalent (safe to drop)

- `model` routing hints (MAF-specific)
- `tools` allowlists (Cowork doesn't gate at this layer)
- Sub-skill manifest listings (directory presence is the mechanism in Cowork)
