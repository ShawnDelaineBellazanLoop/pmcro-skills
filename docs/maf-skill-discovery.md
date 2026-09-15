# MAF skill discovery

MAF file-based providers discover directories containing `SKILL.md`. The provider advertises skill metadata, loads `SKILL.md` when matched, reads skill resources on demand, and runs scripts through a configured runner.

```text
skill-name/
├── SKILL.md
├── assets/
├── references/
└── scripts/
```

Do not assume MAF discovers arbitrary repository files, plugin-root assets, `agents/`, or `.pmcro/` state. The Orchestrator or host adapter must explicitly load those. Discovery does not grant execution permission; script calls still require policy and approval.
