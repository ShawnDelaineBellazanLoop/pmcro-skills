# Intentionally empty

Persona prompts are NOT duplicated here. The acting agent reads them directly, with its
own file-read tool calls, from the single source of truth at the repo root -- there is
no subprocess or script step:

- `agents/orchestrator/AGENT.md` -- the role that embodies this skill (`skills:
  [pmcro-loop]` in its own frontmatter) to dispatch, seal disposition.json on PASS, and
  run O-Mode. Every other role below is dispatched *by* Orchestrator through this skill.
- `agents/planner/AGENT.md`
- `agents/maker/AGENT.md`
- `agents/checker/AGENT.md`
- `agents/reflector/AGENT.md`

This mirrors Anthropic's own skill-creator `agents/` pattern (persona files fed to a
nested `claude -p` subprocess) without forking a second copy of role definitions that
the Orchestrator and this skill would then have to keep in sync by hand.
