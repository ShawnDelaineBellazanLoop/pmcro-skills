# MAF-native workflow and setup

This skill follows Microsoft Agent Framework Agent Skills progressive disclosure:

1. **Advertise:** expose only `name` and `description` from `SKILL.md` frontmatter.
2. **Load:** load `SKILL.md` only after the request matches the description.
3. **Read resources:** read this file, other references, or assets only when required.
4. **Run scripts:** execute a bundled script only after operation selection and approval.

## Resource boundaries

- Put model-facing decisions and stop conditions in `SKILL.md`.
- Put detailed policy and integration notes in `references/`.
- Put machine-consumed defaults, schemas, templates, and fixtures in `assets/`.
- Put deterministic state-changing or verification logic in `scripts/`.

## Request-object contract

Pass only user-specific values in a request JSON object. Scripts load stable defaults from `assets/default-config.json` and validate the request against `assets/request.schema.json` when a schema validator is available. Never ask the model to reproduce a template or default exclusion list.

Example:

```json
{
  "operation": "chain_dump_and_zip",
  "skills_root": "W:\\AgentSkills\\.agents\\skills",
  "output_dir": "W:\\AgentSkills\\.agents\\skills\\output",
  "force": false,
  "dry_run": true
}
```

## Approval policy

Auto-approve `load_skill` and `read_skill_resource` only for trusted local skill directories. Keep `run_skill_script` approval-required by default. Approve script execution only after reviewing the operation, paths, and side effects.

## MAF setup

For file-based skills, configure a `SkillsProvider` or `AgentSkillsProvider` with:

- a skills root containing one directory per `SKILL.md`;
- a script runner for local scripts;
- read-only auto-approval for loading and reading;
- explicit approval for script execution;
- sandboxing, timeouts, allow-listed scripts, and audit logging in production.

In Python, use `SkillsProvider.from_paths(..., script_runner=...)`. In .NET, use `AgentFileSkillsSource` or `AgentSkillsProvider` with `SubprocessScriptRunner.RunAsync`. Do not enable unrestricted script auto-approval for untrusted skills.

## Workflow boundary

Use this skill for selecting and invoking a focused operation. Use an explicit MAF Workflow when the sequence itself must be guaranteed, resumable, or checkpointed. `chain_dump_and_zip.py` is the deterministic implementation of the dump-then-archive sequence.
