# MAF and Agent Skills pattern

MAF exposes file-based skills progressively:

1. **Advertise:** `name` and `description` from frontmatter.
2. **Load:** retrieve the full `SKILL.md` only when the request matches.
3. **Read resources:** retrieve `references/` or `assets/` only when needed.
4. **Run scripts:** execute a bundled script only after selection and approval.

Keep `SKILL.md` below 500 lines. Scripts receive positional arguments as a JSON array of strings in file-based runners. Use a request JSON file when an operation has many values, and let scripts load stable defaults, schemas, and templates from `assets/`.

Production script runners should add sandboxing, timeouts, resource limits, allow-listed scripts, structured logs, and approval for side effects. A skill is appropriate when the agent can choose how to perform a focused task. Use a workflow when the step order must be guaranteed or resumable.
