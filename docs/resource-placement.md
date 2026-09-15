# Resource placement

Put required skill resources beside the skill's `SKILL.md`:

```text
skill-name/assets/
skill-name/references/
skill-name/scripts/
```

Put shared project control-plane state in `.pmcro/` and load it explicitly through the Orchestrator. Put host-specific agent projections and plugin manifests at the plugin root. MAF does not automatically expose arbitrary files in those locations as resources for every skill.
