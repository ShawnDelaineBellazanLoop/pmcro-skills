# dotagent and MAF boundary

`dotagent` and MAF Agent Skills are complementary layers.

## dotagent layer

Use repository-level `.agents/rules/` files for portable shared agent rules. A host adapter can import and export those rules to Claude, Copilot, Cursor, Codex, OpenCode, and other tool-specific formats. Keep private rules in `.agents/rules/private/` or with `.local.md` suffixes.

## MAF skill layer

Use a skill directory with `SKILL.md`, optional `assets/`, `references/`, and `scripts/` for an executable capability exposed through `load_skill`, `read_skill_resource`, and `run_skill_script`.

## Do not merge the layers

Do not put repository rule files inside a skill package unless they are explicitly an asset consumed by the skill. Do not put `SKILL.md` files into `.agents/rules/`. A repository may contain both:

```text
repository/
├── .agents/      # marketplace metadata and repository rules
│   └── rules/
└── plugins/      # MAF Agent Skills packages
```

The MAF provider discovers skills from directories containing `SKILL.md`; the repository rule adapter discovers `.agents/rules/**/*.md`. Keep each layer's frontmatter and discovery rules intact.
