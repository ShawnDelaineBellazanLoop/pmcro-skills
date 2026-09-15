# dotagent boundary

Use `.agents/rules/**/*.md` for repository-wide AI rules, with metadata such as `id`, `scope`, `triggers`, `manual`, `priority`, and `private`. A host adapter can import and export these rules to other assistant formats.

Use MAF Agent Skills for executable capabilities in directories containing `SKILL.md`, with optional `assets/`, `references/`, `scripts/`, and `eval.yaml`.

Keep the layers separate:

```text
repository/
├── .agents/      # marketplace metadata and shared repository rules
│   └── rules/    # shared, scoped, or private repository rules
└── skills/       # MAF Agent Skills packages
```

Do not put `SKILL.md` under `.agents/`, and do not put repository-wide rules inside a skill unless a script explicitly consumes them as an asset.
