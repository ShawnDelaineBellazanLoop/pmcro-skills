# pmcro-skills

[![Catalog CI](https://github.com/ShawnDelaineBellazanLoop/pmcro-skills/actions/workflows/catalog-check.yml/badge.svg)](../../actions/workflows/catalog-check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A standalone, versioned catalog of MAF-native agent skills for the **PMCR-O Colony**
(Plan / Make / Check / Reflect / Orchestrate), built to a package convention similar to
[managedcode/dotnet-skills](https://github.com/managedcode/dotnet-skills) so it can be
consumed by any MAF-based project — not just `ProjectName`. (Note: the original citation
here pointed at a bare, unresolved URL; this link was verified by web search and is the
closest real match found, not a confirmed original source.)

## What lives here

Each skill is a self-contained, declarative capability package:

```text
catalog/<Lane>/<Category>/skills/<skill-name>/
├── manifest.json      # { version, category, packages }
├── SKILL.md            # frontmatter + Trigger On / Workflow / Ralph Loop / Required Result Format
├── scripts/             # executable payload (MAF-invokable)
├── references/          # supporting docs the agent reads, not executes
└── assets/               # templates/static files scripts consume
```

Indexed centrally in [`catalog/skills.json`](catalog/skills.json), validated against
[`catalog/skills.schema.json`](catalog/skills.schema.json).

## What does *not* live here

The five PMCR-O runtime roles — **Orchestrator, Planner, Maker, Checker, Reflector** — are
compiled C# services in the consuming project, not MAF skill packages. They are never
represented here. See `CONTRIBUTING.md` → *Naming Discipline*.

## Plugin Marketplace

This repo is also a real, functioning **Anthropic Claude Code / Cowork plugin
marketplace** — not just a MAF skill catalog. `.claude-plugin/marketplace.json` follows
Anthropic's official marketplace schema (`https://json.schemastore.org/claude-code-marketplace.json`,
the same format used by `anthropics/claude-code` and `anthropics/claude-plugins-official`).
Each of the 5 skills registered in `catalog/skills.json` (`skill-creator`, `git`,
`plugin-packager`, `catalog-check`, `pmcro-loop`) has a matching entry there, using
`strict: false` — meaning `marketplace.json` itself is the authority for each plugin's
definition, so no per-skill `plugin.json` is required.

To install from this marketplace in Claude Code:

```
/plugin marketplace add ShawnDelaineBellazanLoop/pmcro-skills
/plugin install pmcro-loop@pmcro-skills
```

(Substitute any of the other 4 registered skill names for `pmcro-loop` above.)

## Consuming this catalog

`ProjectName\.agents\skills\` pulls from this repo (mechanism TBD: git submodule vs.
sparse-checkout vs. copy-script — tracked as an open decision, same pattern used for the
`dotnet/skills` marketplace integration).

## Status

🚧 Early scaffold. Repo infrastructure (CI, schema, governance) is in place; skill content
(`git`, `docker`, `filesystem`, `playwright`) is being authored incrementally, starting with
`git` as the replacement for the retired `powershell` skill.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the skill-authoring convention and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for participation guidelines. Security issues:
see [`SECURITY.md`](SECURITY.md).

## License

[MIT](LICENSE)
