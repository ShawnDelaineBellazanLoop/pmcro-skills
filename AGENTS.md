# Repository Instructions

This repository contains skill plugins under `plugins/`. Each subdirectory is an independent plugin (`plugins/pmcro`, `plugins/pmcro-csuite`, `plugins/pmcro-skill-creator`, `plugins/pmcro-dotnet`), advertised by the marketplace manifests. `plugins/desktop-commander` is a vendored capability plugin: it executes tools and is outside PMCRO governance, so it may only be invoked through the Orchestrator.

Published skills live under `plugins/<plugin>/skills/<skill>/`. `.agents/skills/` is reserved for local, authoring-only skills. Do not duplicate a published skill there — one source of truth, and the plugin package is the distributable one.

## Verify before and after

```bash
python .pmcro/tests/run_all.py
```

One entry point, on purpose: gate tests, the host-boundary preflight, marketplace manifest sync, the content manifest, and contract validation for every frame and checkpoint. A cycle that accepts on a partial check has certified work it never examined.

After changing any tracked file, regenerate the content manifest:

```bash
python .pmcro/scripts/manifest.py --write
```

## The control plane governs itself

`.pmcro/` is not documentation. `.pmcro/policies/resource-operations.json` decides `allow`, `approval`, or `deny` per resource per verb, and three places read it: `resource_ops.py`, the `Write`/`Edit` hook in `plugins/pmcro/scripts/control_plane_guard.py`, and the .NET runtime. A resource the table does not describe is denied, so forgetting to declare one fails closed.

What that means in practice:

- **Frames and events are append-only.** A correction is a new frame referencing the wrong one, never an edit. If a refusal blocks you, the refusal is the feature — do not edit the file directly to get around it.
- **Laws and contracts need a person.** Changing `.pmcro/laws/constitution.md` or adding a schema returns approval-required. Ask; do not pass `--approved` on your own authority, because that flag records that a human agreed.
- **Claim work before starting it.** `python .pmcro/scripts/checkpoint.py claim "<what>"`, then `release` when done. An unreleased claim is retained as abandoned, which is what tells the next session a run did not finish.

Read the laws through the skill rather than from memory:

```bash
python .pmcro/scripts/resource_ops.py laws read
```

## Working on skills

Use `plugins/pmcro-skill-creator/skills/create-skill` for scaffolding, and follow its package contract: `SKILL.md` routes, `references/` holds detail loaded on demand, `assets/` holds machine-consumed data, `scripts/` holds deterministic execution. That split is not decoration — a frontier model infers a missing tier and hides the gap, and a small local model improvises silently instead of reporting it.

Every skill declares its tool authority in frontmatter: `tools: none` for anything that executes nothing, or `tool_authority: orchestrator-only` to defer. The preflight fails a governed skill that declares neither.

Skills that generate code should have the model fill a validated spec and a script render the output. Do not ask a model to emit code it cannot check.

## The .NET track

`dotnet/skills` is extended, never forked. Their plugins carry general .NET guidance and move on their own schedule; ours carry house patterns. They compose as separate plugins — depend on `dotnet-template-engine` for templating rather than reimplementing it.

Version-sensitive facts are checked against nuget.org and Microsoft Learn, not recalled. Package families move in lockstep: Aspire and Microsoft Agent Framework each share internal APIs that semver ranges do not cover, and a partial bump throws at runtime rather than failing the build.
