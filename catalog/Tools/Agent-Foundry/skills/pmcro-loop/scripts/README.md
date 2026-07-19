# Intentionally empty

`pmcro-loop` has no scripts. In a live Claude Code / Cowork / MAF-loaded session, the
current agent creates frame files directly with its own file-write tool calls, following
whichever `agents/{role}/AGENT.md` persona it is currently embodying — there is no
subprocess step to shell out to.

(This differs from Anthropic's own skill-creator, whose `scripts/run_eval.py` genuinely
needs an isolated nested `claude -p` process to test trigger behavior objectively. PMCR-O
frame creation has no such isolation requirement — the acting agent just writes what it
produces.)
