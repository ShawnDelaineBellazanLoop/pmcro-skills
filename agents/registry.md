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
| EC-004 | Maker | Maker does not self-score / does not assume Checker role |
| EC-009 | Checker, Reflector | MaxLoops enforced — no infinite retry on a bad result |

## Not In This Registry
- `catalog/*` — reusable capability packages (docker, filesystem, git, playwright,
  etc.). Discovered by MAF's AgentSkillsProvider, not referenced here.
- Trails — business-process definitions that compose skills; live under the consuming
  project's `.pmcro\trails\`, not under `agents/`.
- Frames, memory, knowledge — per-project runtime state; live under the consuming
  project's `.pmcro\`, not in this catalog repo. This registry describes the roles
  themselves, which are portable; the state they produce is not.
