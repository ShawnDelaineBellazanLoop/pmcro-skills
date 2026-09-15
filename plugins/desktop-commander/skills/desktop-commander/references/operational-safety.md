# Operational safety

- Resolve every input path before use and reject missing roots.
- Do not follow symlinks unless explicitly requested.
- Never overwrite an existing output without `--force`.
- Keep archive member names relative, normalized, and traversal-free.
- Use UTF-8 text with LF line endings for dumps.
- Exclude `.git`, `.vs`, `__pycache__`, archives, temporary files, and bytecode by default.
- Do not place secrets in command arguments, dumps, manifests, or reports.
- Validate output existence, size, hash, and readability before reporting success.
- Use `--dry-run` before a large or unfamiliar operation.

## Exit behavior

Exit zero only after the postcondition is verified. Exit non-zero for invalid paths, collisions, permission errors, decoding failures that affect required output, or archive-integrity failures.
