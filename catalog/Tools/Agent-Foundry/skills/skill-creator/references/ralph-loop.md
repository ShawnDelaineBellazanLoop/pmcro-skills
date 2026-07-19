# Ralph Loop — One Authoring Methodology, Not the Architecture

This is a reference, not a foundation. `skill-creator`'s central concept is the PMCR-O
lifecycle (Observe → Plan → Create → Check → Reflect → Publish → Exercise → Learn). The
Ralph Loop is one technique that can be applied *during* the Create/Check/Reflect portion
of that lifecycle — cite it here, don't architect around it, so this document can be
swapped out later without touching `SKILL.md` itself.

## What It Is

A pattern popularized by Geoffrey Huntley (and extended by others, e.g. Dex Horthy's RPI —
Research, Plan, Implement — variant): run an agent in a loop where each iteration picks
one bounded task, implements it, validates the result, commits if checks pass, then resets
context before the next iteration. The point is managing context rot — long-running
sessions degrade, so the loop trades session length for repeated fresh starts anchored to
a persisted plan on disk.

Shape of one iteration:

1. Compare the current state against the plan/spec.
2. Pick exactly one task.
3. Implement it.
4. Validate (tests, lint, schema check — whatever "done" means for that task).
5. Commit if valid; otherwise fix and re-validate before moving on.
6. Reset context, repeat with the next task.

## Where It Maps Onto PMCR-O

| Ralph Loop step | PMCR-O equivalent |
|---|---|
| Compare state vs. plan | Plan |
| Implement one task | Create / Make |
| Validate | Check |
| Fix and re-validate | Reflect (bounded — see `EC-009`, max 3 loops) |
| Commit | Publish |
| Reset context | Session boundary — this is why trails persist to disk rather than relying on conversation memory |

## Why It's Cited Here Rather Than Made Central

An authoring methodology can change — a different technique might replace the Ralph Loop
next year. If `skill-creator`'s `SKILL.md` were built *around* Ralph Loop terminology,
every future methodology change would require rewriting the skill's identity. Because the
citation lives here instead, updating this one file is enough.

## Coordinating Many Loops

The advanced version of this pattern — coordinating many autonomous loops into a
self-managing system rather than running one at a time — is sometimes called "Gas Town"
in the source material. That coordination layer is structurally what the Colony's
Orchestrator + Chief dispatch architecture already does (Chiefs run their own sealed
Plan→Make→Check→Reflect cycles, delegating execution into a shared subject-agent pool).
Don't rebuild that coordination logic inside a skill — it already exists at the runtime
layer.
