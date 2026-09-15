---
name: create-skill
description: "Create or update MAF-compatible Agent Skills with deterministic scripts, on-demand references, machine-consumed assets, evaluation fixtures, and dotagent-compatible repository boundaries. Use when scaffolding a new skill or converting an existing skill to the Agent Skills specification. Do not use for fixing an evaluated skill without changing its structure; use the quality-improvement workflow instead."
license: MIT
compatibility: "MAF Agent Skills-compatible local skill authoring workflow. Requires filesystem access; runtime validation may require Python, Node.js, or dotnet depending on the generated skill."
metadata:
  author: "local-agent-skills"
  version: "1.0.0"
  protocol: "maf-agent-skills"
  compatible_with: "dotagent"
---

# Purpose

Create small, verifiable, local-model-friendly Agent Skills. Separate model instructions from executable logic, stable machine data, and detailed references so MAF can progressively disclose and safely execute each part.

## When to Use

- Create a new skill package from a concrete workflow.
- Convert an existing skill to MAF Agent Skills format.
- Add deterministic scripts, references, assets, or evaluation fixtures.
- Align a skill repository with dotagent without mixing repository rules into skill packages.

## When Not to Use

- Do not use for repository-wide rules alone; use the repository's `.agents/rules/` structure.
- Do not use to silently rewrite a working skill after a one-off preference.
- Do not include resources that are not real files or are not linked from `SKILL.md`.

## Required package contract

```text
skill-name/
├── SKILL.md
├── eval.yaml                 # optional local fixture; marketplace evals live under tests/
├── assets/                   # required when stable machine data exists
├── references/               # required when detailed policy exists
└── scripts/                  # required when deterministic execution exists
```

Create only directories that contain real resources, but include all three resource types when the workflow depends on scripts, policy, and static data.

## Workflow

1. **Specify:** capture the inputs, desired output, edge cases, side effects, and concrete examples.
2. **Name:** use lowercase letters, numbers, and single hyphens; match the directory name; stay within 64 characters.
3. **Route:** write a specific description stating what the skill does, when to use it, and the nearest cases not to use it for.
4. **Partition:** keep routing and core decisions in `SKILL.md`; put detailed rules in `references/`, static schemas/templates/defaults in `assets/`, and deterministic operations in `scripts/`.
5. **Design for MAF:** support advertise → load → read resources → run scripts. Document script argument contracts; prefer one validated request object for many inputs.
6. **Design for repository rules:** keep `.agents/rules/**/*.md` separate from skill packages. Do not place `SKILL.md` under `.agents/`.
7. **Implement:** create self-contained scripts with stable paths derived from the script location, explicit overwrite policy, deterministic ordering, structured output, and non-zero failure exits.
8. **Evaluate:** add at least five distinct `eval.yaml` stimuli for model-invocable skills, or mark a helper skill as non-invocable and test it through its consumers.
9. **Validate:** check frontmatter, links, resource existence, line count, script syntax, postconditions, and truthful failure reporting.
10. **Test:** run the skill with a real workflow, inspect the generated artifact, and patch the source skill when a reusable defect is discovered.
