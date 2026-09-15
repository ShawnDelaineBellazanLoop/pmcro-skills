# Contributing

Keep plugin manifests consistent across the root, `.claude-plugin`, and `.codex-plugin` locations. Every model-invocable skill must include an `eval.yaml` under `tests/` with at least five distinct stimuli.

Keep `SKILL.md` under 500 lines, use relative resource links, and separate repository `.agents/rules/` files from MAF skill packages. Do not include secrets or unverified claims of runtime validation.
