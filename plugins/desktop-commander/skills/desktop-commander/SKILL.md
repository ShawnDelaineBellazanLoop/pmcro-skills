---
name: desktop-commander
description: "Use for deterministic, auditable desktop and filesystem operations, including skill-folder dumps, single-skill exports, reproducible ZIP archives, process or window control, clipboard and input automation, event listening, and manual-operation fallbacks. Do not use for unrestricted destructive automation or unverified claims of success."
license: MIT
compatibility: "MAF Agent Skills-compatible file-based skill. Requires a configured local script runner with Python 3 for bundled scripts."
metadata:
  author: "local-agent-skills"
  version: "1.1.0"
  protocol: "maf-agent-skills"
  resource_layout: "assets-references-scripts"
version: 1.1.0
---

# Purpose

Provide a local-model-friendly, deterministic operating procedure for desktop, filesystem, process, clipboard, input, event-listening, logging, and skill-package operations. Prefer bundled scripts and references over regenerated code so the same request produces the same verifiable result.

## When to Use

- Dump an entire skills root or one skill folder into a text artifact.
- Create or verify a reproducible ZIP archive.
- Perform an explicitly authorized filesystem, process, window, clipboard, input, or event-listening operation.
- Produce an audit trail or manual fallback command for an unavailable integration.

## When Not to Use

- Do not use for unrestricted deletion, overwriting, credential collection, or hidden input capture.
- Do not report success when a command failed or its output was not reopened and checked.
- Do not replace a specialized integration when one is available and safer.

## Inputs

| Input | Required | Description |
|---|---:|---|
| Operation | Yes | The specific dump, archive, or authorized desktop action. |
| Absolute source path | Yes for file operations | Existing file or directory to inspect or operate on. |
| Absolute output path | Yes for generated artifacts | Destination; existing files require `--force`. |
| Exclusions | No | Explicit additional glob patterns; built-in noise exclusions remain active. |
| Dry run | No | Preview selected files and outputs without mutation. |

## Workflow

1. **Plan:** identify the operation, absolute paths, exclusions, overwrite policy, and risk.
2. **Make:** create a small request object for variable values and call [run_operation.py](scripts/run_operation.py), or call the smallest bundled script directly; use `--dry-run` first when scope is unfamiliar.
3. **Check:** verify output existence, non-zero size where required, file count, SHA-256, readable content, and path containment.
4. **Reflect:** record failures, deviations, and operator corrections in the report; never hide an error.
5. **Orchestrate:** chain only verified stages and stop on the first failed checkpoint.

## PMCRO Checkpoints

- **Planner:** scope and safety constraints confirmed.
- **Maker:** one deterministic operation executed.
- **Checker:** ground truth independently verified.
- **Reflector:** outcome and deviations recorded.
- **Orchestrator:** dependent work proceeds only after the prior checkpoint passes.

## Bundled Scripts

- [dump_skill_folder.py](scripts/dump_skill_folder.py) - Dump all readable files under a skills root.
- [dump_single_skill.py](scripts/dump_single_skill.py) - Dump one named or path-selected skill.
- [zip_skill.py](scripts/zip_skill.py) - Create a stable ZIP with a manifest.
- [chain_dump_and_zip.py](scripts/chain_dump_and_zip.py) - Generate and verify `skills_dump.txt` and `skills_dump.zip`.
- [common.py](scripts/common.py) - Shared path, exclusion, hash, and reporting helpers.

## Bundled References and Assets

- [Operational safety](references/operational-safety.md) - Path, overwrite, symlink, archive, and reporting rules.
- [PMCRO checkpoints](references/pmcro-checkpoints.md) - Lifecycle checkpoint contract.
- [Package manifest schema](assets/package-manifest.schema.json) - Machine-readable report contract.
- [Evaluation fixture](eval.yaml) - Local regression cases for routing and output verification.

## Validation

A successful operation must satisfy all applicable checks: the output exists; it is readable; it is not unexpectedly empty; its hash is recorded; relative paths are normalized; no symlink or traversal was followed; and ZIP files reopen without absolute, duplicate, or traversal members. Return a non-zero exit status for any failed check. For MAF, auto-approve `load_skill` and `read_skill_resource` only for trusted local sources; keep `run_skill_script` approval-required by default.

## Common Pitfalls

| Pitfall | Required response |
|---|---|
| Output already exists | Stop and require `--force`; never overwrite silently. |
| Python launcher unavailable | Report the exact missing prerequisite and provide the manual command; do not claim runtime validation. |
| Binary or non-UTF-8 input | Include a deterministic omission marker and preserve hash/size metadata. |
| Archive contains unsafe names | Reject the archive and report the offending member. |
| Integration unavailable | Stop before mutation and provide a manual fallback with expected postcondition. |

## Security and Manual Fallback

Do not follow symlinks by default. Reject traversal after path resolution. Do not expose secrets in logs. Require explicit confirmation for destructive operations. If an integration is unavailable, present the exact command, absolute paths, expected result, and verification command for operator execution.
Fallback

Do not follow symlinks by default. Reject traversal after path resolution. Do not expose secrets in logs. Require explicit confirmation for destructive operations. If an integration is unavailable, present the exact command, absolute paths, expected result, and verification command for operator execution.
