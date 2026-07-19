---
name: pmcro-loop
description: "Teaches an agent how to run one PMCR-O cycle and write its output as a sealed Trail. Use whenever the Orchestrator (agents/orchestrator/AGENT.md) has dispatched to Planner, Maker, Checker, or Reflector and that role needs to know exactly what file to write, in what format, and where. DO NOT USE FOR: deciding *whether* to start a cycle, which Trail applies, or dispatch order -- that's the Orchestrator's own O-Mode reasoning, not this skill's job. DO NOT USE FOR: implementing the compiled runtime -- this is the session-level equivalent for Claude Code/Cowork/claude.ai, not a replacement for W:\\ProjectName's C# OrchestratorService."
compatibility: "No runtime dependency. In Claude Code/Cowork, the acting agent writes trail files directly via its own filesystem tools. Persona content is read from the repo-root agents/{role}/AGENT.md files, not duplicated here."
---

# PMCR-O Loop

## Trigger On
- The Orchestrator has just dispatched to a role and that role needs its output format
- "start a trail for X" / "run a PMCR-O cycle on X"
- "what does Checker actually write when it issues a verdict?"
- Resuming a trail after a session boundary (need to know what state to read first)

## Usage
```
/pmcro-loop <role> [trail-id]
```
- `<role>` -- optional. One of `planner`, `maker`, `checker`, `reflector`. If given,
  skip role inference entirely and go straight to Step 1 with this role.
- `[trail-id]` -- optional. The `{uuid}` of an existing trail to resume. If omitted
  with a role given, start a new trail. If both are omitted, fall back to inference
  (Step 0).

Examples:
- `/pmcro-loop planner` -- start a new trail, act as Planner
- `/pmcro-loop checker a1b2c3d4-...` -- resume trail `a1b2c3d4-...`, act as Checker
- `/pmcro-loop` (no args) -- infer the role from context per Step 0

## Value
- Gives every role a single, unambiguous answer to "what do I write, and where" --
  removes the ambiguity between "I did the work" (conversational) and "I produced a
  Frame" (a real file another session or role can read).
- Makes a cycle resumable across a session cutoff: any session can pick up a trail by
  reading its files, without depending on the prior session's conversational memory.
- Keeps role definitions single-sourced. This skill does not fork a copy of
  Planner/Maker/Checker/Reflector -- it points at the same `agents/{role}/AGENT.md`
  files the Orchestrator already dispatches to.

## Do Not Use For
- Deciding reasoning strategy, execution topology, or which Trail applies -- that's
  O-Mode, internal to the Orchestrator, not this skill.
- The actual compiled runtime in `W:\ProjectName` -- that's real C# services via MAF,
  not a Claude session following markdown.

## How This Differs From Anthropic's skill-creator `agents/` Pattern
Anthropic's own skill-creator ships persona files under `agents/` (analyzer, comparator,
grader) that its `scripts/` subprocess out to a nested `claude -p` call per persona,
because it needs a genuinely isolated session to test trigger behavior objectively.
PMCR-O has no such isolation requirement -- there is exactly one acting agent per role at
a time, embodying that role directly. So `pmcro-loop` has no `agents/` folder and no
scripts: the acting agent reads the role's `AGENT.md` from the repo root and writes the
frame itself. See `agents/README.md` in this skill and `scripts/README.md` for why those
folders are intentionally near-empty.

## Process

### Step 0: Resolve the Role (only if not given explicitly)
- If `/pmcro-loop <role>` was invoked with an explicit role argument, use it directly
  and skip this step entirely -- do not re-infer or second-guess an explicit argument.
- Otherwise, infer the role in this order:
  1. If a `trail-id` was given, read that trail's latest `NN-*.jsonl` file present. The
     next role is whichever one hasn't written yet for the current cycle number (e.g.
     if `01-plan.jsonl` exists but `01-make.jsonl` doesn't, the role is Maker).
  2. If no `trail-id` was given but conversation context makes the active role
     unambiguous (e.g. the Orchestrator just said "dispatching to Checker"), use that.
  3. If still ambiguous, ask exactly one question: which role, for which trail --
     don't guess and don't silently default to Planner.
- An explicit role argument always wins over inference. This is what makes a session
  resumable without depending on the prior session's conversational memory being
  intact -- `/pmcro-loop checker <trail-id>` alone is enough to pick up exactly where a
  cut-off session left off.

### Step 1: Identify the Role and the Trail
- Read the SeedIntentFrame (`00-frame.json`) if the trail already exists, or create it
  if this is cycle 1 of a new trail (see `assets/00-frame.template.json`).
- Confirm `{source-type}` and `{uuid}` per `references/trail-schema.md`.

### Step 2: Read the Role Definition
- Read `agents/{role}/AGENT.md` at the repo root for whichever role is dispatched
  (`planner`, `maker`, `checker`, or `reflector`). That file defines what the role Owns,
  Does Not Own, and any role-specific invariants.

### Step 3: Do the Role's Work
- Perform the actual work the role owns (plan / make / score / reflect).
- Maker: cite real evidence (command output, file diffs, verified state), not just
  claims -- per EC-VERIFY-FIRST-001.
- Checker: score against defined criteria only; a below-threshold criterion is an
  automatic LOOP, not a judgment call.

### Step 4: Write the Frame
- Copy the matching template from `assets/` (`NN-plan.template.jsonl`,
  `NN-make.template.jsonl`, `NN-check.template.jsonl`, or `NN-reflect.template.jsonl`),
  fill in every field -- no `<placeholder>` left unresolved (PLAN-001) -- and write it to
  `.pmcro/trails/{source-type}/{uuid}/{NN}-{role}.jsonl` per `references/trail-schema.md`.

### Step 5: Check MaxLoops Before Looping
- If Checker's verdict is LOOP, confirm `loop_count` is still under MaxLoops (EC-009)
  before Reflector runs and a new cycle starts. At MaxLoops, halt and surface to the
  human rather than looping again.

### Step 6: Seal on PASS
- On a PASS verdict, write `disposition.json` at the trail root from
  `assets/disposition.template.json`. Once written, treat every frame in the trail as
  immutable -- anything noticed afterward goes in `open_hypotheses`, not a frame edit.

## Output Format
See `references/trail-schema.md` for the full schema of every file type. All frame files
are the acting agent's own direct file writes -- there is no intermediate parsing step
and no subprocess output to capture.

## References
- `references/trail-schema.md` -- full trail directory layout and per-file JSON schema
- `agents/README.md` -- why persona files are not duplicated in this skill
- `scripts/README.md` -- why this skill has no scripts

## Law Anchors
| Law | Enforced By | Meaning |
|---|---|---|
| PLAN-001 | Planner | No `<placeholder>` values in any frame |
| EC-VERIFY-FIRST-001 | Maker | Evidence, not just claims, in `NN-make.jsonl` |
| EC-004 | Checker | Checker alone issues verdicts -- Maker never self-scores |
| EC-009 | Checker/Reflector | MaxLoops enforced before another cycle starts |
