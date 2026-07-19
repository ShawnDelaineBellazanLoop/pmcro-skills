# Trail & Frame Schema

Defines what a PMCR-O agent writes to disk during a cycle, and where. This is what the
`pmcro-loop` skill teaches an agent to produce — whichever role's `AGENT.md` it is
currently embodying.

## Directory Layout

```
.pmcro/trails/{source-type}/{uuid}/
├── 00-frame.json         ← SeedIntentFrame: the goal this trail resolves
├── 01-plan.jsonl         ← Planner's output for cycle 1
├── 01-make.jsonl         ← Maker's output for cycle 1
├── 01-check.jsonl        ← Checker's verdict for cycle 1
├── 01-reflect.jsonl      ← Reflector's output for cycle 1 (present only on LOOP)
├── 02-plan.jsonl         ← cycle 2, if Checker issued LOOP on cycle 1
├── ...
└── disposition.json      ← written once, at the root, to seal the trail
```

- `{source-type}` groups trails by what kind of work produced them (e.g. `conversation-ingestion`,
  `skill-authoring`, `catalog-maintenance`). Use a short kebab-case label describing the
  work, not the tool that did it.
- `{uuid}` is a fresh UUID per trail, generated once at cycle start (`python3 -c "import
  uuid; print(uuid.uuid4())"` or the language-appropriate equivalent).
- Cycle number (`01`, `02`, ...) increments only on a LOOP verdict. A trail that passes
  on the first cycle has only `01-*` files.

## File Formats

### `00-frame.json` (SeedIntentFrame)
```json
{
  "trail_id": "<uuid>",
  "source_type": "<source-type>",
  "created_at": "<ISO-8601 timestamp>",
  "goal": "<one-sentence statement of what this trail resolves>",
  "context": "<why this trail exists — what triggered it>",
  "trail_convention": "<which named Trail/procedure applies, if known>",
  "raw_seed_intent": "<optional — the person's original, unedited input (e.g. verbatim voice-to-text) when it differs from goal>",
  "true_intent": "<optional — present only if Orchestrator ran True Intent extraction on a messy raw_seed_intent; see agents/orchestrator/AGENT.md's O-Mode section>"
}
```
`raw_seed_intent` and `true_intent` are optional and only appear together — if the
original intent was already clear, omit both rather than duplicating `goal`. Per
OMODE-001 (`agents/registry.md`), only the Orchestrator may populate `true_intent`;
no other phase performs this extraction, because only the Orchestrator is permitted to
loop internally (Invariant 3/5 — see `pmcro-loop-core-invariants.md` in
`B:\pmcro-cline\.pmcro\context\`, the source this pattern is adapted from).

### `NN-plan.jsonl` (one line per planning decision, Planner-owned)
```json
{"step": 1, "action": "<what>", "rationale": "<why>", "skill": "<catalog skill name, or null>", "needs_new_skill": false, "depends_on": []}
```
Every value must be fully resolved — no `<placeholder>` text (PLAN-001). A plan
containing unresolved placeholders is not a valid PlannerFrame.

Per PLAN-002 (`agents/planner/AGENT.md`), `skill` must name a real entry in
`catalog/skills.json`, matched against that skill's `USE FOR` / `DO NOT USE FOR`
phrasing. If no skill matches, set `skill: null` and `needs_new_skill: true` — this
surfaces a genuine catalog gap instead of Planner inventing a workaround step. A step
may never name a role (Maker/Checker/Reflector) as its `skill`. Steps that are inherent
verification practice rather than delegated capability work (e.g. re-reading a file to
confirm an edit landed, per EC-VERIFY-FIRST-001) may set `skill: null,
needs_new_skill: false` — this exception is noted here because PLAN-002's original
wording only defined the `true` case explicitly.

### `NN-make.jsonl` (one line per unit of work produced, Maker-owned)
```json
{"step": 1, "evidence": "<what was actually produced/verified — command output, file diff, etc.>", "claim": "<what this step accomplishes>"}
```
Maker records evidence, not just claims (EC-VERIFY-FIRST-001). Maker does not include a
PASS/LOOP verdict — that's Checker's job alone (EC-004).

### `NN-check.jsonl` (single line, Checker-owned)
```json
{"verdict": "PASS", "criteria": [{"name": "<criterion>", "passed": true, "evidence": "<citation into make.jsonl>"}], "loop_count": 1}
```
A verdict of `LOOP` is automatic (not a judgment call) if any required criterion's
`passed` is `false`. `loop_count` is checked against MaxLoops (EC-009) before another
cycle is allowed to start.

### `NN-reflect.jsonl` (present only when the prior check was LOOP, Reflector-owned)
```json
{"trigger": "<what failed and why>", "constraint_id": "EC-<domain>-<NNN>", "binding": "<the rule that prevents recurrence, written so Planner/Maker can follow it directly>"}
```

### `disposition.json` (root of the trail, written once to seal it)
```json
{"sealed_at": "<ISO-8601 timestamp>", "final_verdict": "PASS", "total_cycles": 1, "earned_constraints": ["EC-<domain>-<NNN>"], "open_hypotheses": [], "next_seed_intent": null}
```
Sealed trails are immutable — frames are left as-is after sealing. Anything noticed
after the fact goes in `open_hypotheses`, not a frame edit.

## Trail Chaining (`next_seed_intent`)
`next_seed_intent` is an optional field on `disposition.json`, written at seal time only.
When the work that just sealed makes the next piece of work obvious, name it instead of
leaving discovery to whoever reads the trail later:
```json
"next_seed_intent": {"goal": "<one-sentence goal for the follow-on trail>", "source_type": "<suggested source-type>", "trigger": "<optional: correction | refinement | informational>"}
```
`trigger` is optional and classifies *why* the next trail is being named, matching
the Reflector-Retry-vs-O-Mode distinction: `correction` means Reflector diagnosed a
specific failure and the next trail exists to fix it; `refinement` means Orchestrator's
O-Mode judged the sealed work correct but worth deepening (success-driven, exploratory,
never mandatory); `informational` is the default when neither applies -- a follow-on
worth naming but not urgent. This is a classification addition only, not a new
mechanism -- `next_seed_intent` itself already existed before this trail.

Leave it `null` when there's no clear follow-on — don't invent one to fill the field
(that's the same PLAN-001 placeholder problem, just at the trail level instead of the
step level). This is the session-level equivalent of the compiled `W:\ProjectName`
runtime's Succession Law / NextSeedIntent Baton pattern, scoped down: this skill only
names the next goal. It does not implement MaxChainedTrails or autonomous unattended
chaining — that machinery belongs to the compiled OrchestratorService, not to a Claude
session following markdown (see `SKILL.md`'s Do Not Use For section). A human or the
Orchestrator still decides whether to actually start the named trail.

Because sealed trails are immutable, a trail can never be edited after the fact to add
a `next_seed_intent` it didn't originally have — if that's needed, name it in the next
trail's own `00-frame.json` context instead, pointing back at the trail it follows.

## Cross-Session Continuity
If a session ends mid-cycle, the next session's first move is to read `00-frame.json`
and the latest `NN-*.jsonl` files in the trail directory to determine which role's turn
is next — not to restart the trail from scratch.
