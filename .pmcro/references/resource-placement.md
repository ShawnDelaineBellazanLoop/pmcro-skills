# Resource placement and MAF discovery

## Skill-level resources

Place resources required by one skill beside its `SKILL.md`:

```text
skill-name/
├── SKILL.md
├── assets/
├── references/
└── scripts/
```

MAF file-based providers discover skills from `SKILL.md`, expose recognized resource files on demand, and expose recognized scripts through the configured script runner. Search depth, extensions, and filters are host configuration; do not assume every file is exposed.

## Plugin-level resources

Use plugin-root `agents/`, shared adapter code, and manifests for host integration. MAF does not automatically expose arbitrary plugin-root files as resources of every skill. An adapter must explicitly load and validate them.

## Repository-level resources

Use `.pmcro/` for laws, schemas, Trail frames, events, earned constraints, queue state, and handoffs. The Orchestrator loads these explicitly. They are project control-plane state, not automatically discovered skill resources.

## Rule

If a skill cannot work correctly without a file, keep that file in the skill package and link it from `SKILL.md`. If a file is shared runtime state, keep it in `.pmcro/` and define an explicit loader contract.
