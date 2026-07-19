# Registry

## Purpose
Index of the PMCR-O runtime roles and the laws/constraints that bind them. Read by the
Orchestrator (and by any human or session picking up an interrupted Trail) as the single
source of truth for "what exists and what governs it."

## Roles
| Role | File | Owns |
|---|---|---|
| Orchestrator | orchestrator/AGENT.md | High-level goal, O-Mode, dispatch, SeedIntentFrame |
| Planner | planner/AGENT.md | execution_plan_json |
| Maker | maker/AGENT.md | Execution, evidence |
| Checker | checker/AGENT.md | Scoring, PASS/LOOP verdict |
| Reflector | reflector/AGENT.md | EarnedConstraints on LOOP |

## Law Anchors
| Law | Enforced By | Meaning |
|---|---|---|
| §5.1 Portability Law | All roles | No literal drive-letter paths in any rule file — all paths workspace-root-relative |
| PLAN-001 | Planner | No `<placeholder>` values in execution_plan_json |
| PLAN-002 | Planner | Every execution_plan_json step resolves to a real catalog skill or is flagged needs_new_skill — never routed to a role instead |
| EC-004 | Maker | Maker does not self-score / does not assume Checker role |
| EC-009 | Checker, Reflector | MaxLoops enforced — no infinite retry on a bad result |
| TRAIL-001 | All roles | Every substantive edit to this repo is captured as a sealed trail under `.pmcro/trails/` before the session ends — standing convention, not a Reflector-minted EarnedConstraint |
| OMODE-001 | Orchestrator | True Intent extraction (raw_seed_intent → true_intent) is performed only by the Orchestrator — no other phase interprets raw input, because only the Orchestrator is permitted to loop |
| OMODE-002 | Orchestrator | True Intent extraction is bounded — convergence or a hard cap of 3 passes, whichever comes first; never an unbounded loop, even at the one phase allowed to loop |
| OMODE-003 | Orchestrator | O-Mode discretionary refinement (post-PASS, exploratory) is distinct from Reflector's Retry (post-LOOP, corrective) — never conflate the two, never let refinement skip HIL/TYPE1 gates or touch a sealed trail's frames |

## Not In This Registry
- `catalog/*` — reusable capability packages (docker, filesystem, git, playwright,
  etc.). Discovered by MAF's AgentSkillsProvider, not referenced here.
- Trails — business-process definitions that compose skills; live under the consuming
  project's `.pmcro\trails\`, not under `agents/`.
- Frames, memory, knowledge — per-project runtime state; live under the consuming
  project's `.pmcro\`, not in this catalog repo. This registry describes the roles
  themselves, which are portable; the state they produce is not.
