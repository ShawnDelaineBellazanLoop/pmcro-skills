---
name: pmcro-resource
description: "Read or change anything in the PMCRO control plane - laws, earned constraints, TrailFrames, trail events, checkpoints - through one policy-gated CRUD interface. USE FOR: listing or inspecting laws and constraints, recording a frame or event, advancing a checkpoint, asking whether an operation is even permitted ('can I edit a frame?', 'why was that rejected?'), or auditing which operations a resource allows. Use it whenever work touches .pmcro state, including when the request names the resource without naming a verb. DO NOT USE FOR: dispatching PhaseMessages or draining the queue (use pmcro-orchestrator's runtime boundary), or editing ordinary project files that are not control-plane state."
license: MIT
compatibility: "Requires Python 3.11+ and a .pmcro control plane in the repository. Standard library only - no package installs."
metadata:
  protocol: pmcro
  tool_authority: orchestrator-only
---

# PMCRO resource operations

Four verbs, one policy table. `create`, `read`, `update`, `delete` mean the same
thing everywhere; what differs is which verbs a resource refuses and why. That
table lives in `.pmcro/policies/resource-operations.json` and is read by this
skill, by the .NET runtime, and by anything else that touches the control plane,
so all of them refuse the same things for the same reasons.

## When to use

- Listing or reading laws, constraints, frames, events, or checkpoints.
- Recording a new frame or event, or advancing a checkpoint.
- Finding out whether an operation is allowed before attempting it.
- Explaining a refusal to someone who expected the operation to work.

## When not to use

- Delivering a PhaseMessage or draining the queue - that is the dispatcher, in
  `pmcro-orchestrator`'s [runtime boundary](../pmcro-orchestrator/references/runtime-boundary.md).
- Editing source files, docs, or anything outside `.pmcro/`.

## The three decisions

| Decision | Meaning | What to do |
|----------|---------|------------|
| `allow` | Proceed under normal policy. | Run it. |
| `approval` | Legitimate, but a human authorizes it first (LAW-008). | Ask the person, then re-run with `--approved`. |
| `deny` | Never valid for this resource. | Do not retry, reframe, or route around it. Report the reason. |

A `deny` reason always names the rule behind it. "Frames cannot be updated" is
not a quirk of the implementation; it is LAW-010, and a correction is a new frame
that references the prior one.

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| resource | Yes | `laws`, `constraints`, `frames`, `events`, `checkpoints`, or `policy` to print the whole matrix |
| operation | No | `create`, `read` (default), `update`, `delete` |
| `--id` | For update, and for reading one record | Record id: `LAW-010`, `ARCH-007`, `frame-...`, `checkpoint-...` |
| `--data` / `--file` | For create and update | JSON payload, inline or from a file |
| `--approved` | Only when the decision is `approval` | Records that a human authorized this change |

## Workflow

### Step 1: Check the table before promising anything

```bash
python .pmcro/scripts/resource_ops.py policy
```

Do this when you are unsure whether an operation is permitted. Telling someone
you will edit a frame and then discovering you cannot is worse than checking.

### Step 2: Run the operation

```bash
python .pmcro/scripts/resource_ops.py laws read
python .pmcro/scripts/resource_ops.py laws read --id LAW-010
python .pmcro/scripts/resource_ops.py constraints create --data "{\"id\":\"ARCH-020\",\"rule\":\"...\",\"status\":\"candidate\"}"
python .pmcro/scripts/resource_ops.py checkpoints update --id checkpoint-x --data "{\"next_phase\":\"checker\"}"
```

### Step 3: Read the exit code as the decision

| Code | Meaning | Response |
|------|---------|----------|
| 0 | Done | Report what changed |
| 1 | Bad input or contract violation | Fix the payload; the errors name the fields |
| 2 | Denied by policy | Report the reason and stop |
| 3 | Not found | Check the id against a `read` listing |
| 4 | Approval required | Ask the person, then re-run with `--approved` |
| 5 | Governed but no store yet | Say so; do not hand-edit files and call it done |

### Step 4: Let the evidence write itself

Successful mutations append a trail event automatically. Reads write nothing - a
trail that records every glance stops being a record of work.

## Validation

- [ ] A `deny` was reported with its reason, not worked around by editing the file directly
- [ ] An `approval` decision reached a human before `--approved` was used
- [ ] After a mutation, `.pmcro/trails/events.jsonl` has a new line
- [ ] `python .pmcro/tests/test_resource_ops.py` passes

## Common pitfalls

| Pitfall | Instead |
|---------|---------|
| Editing `.pmcro/trails/frames/*.json` by hand after a `deny` | The refusal is the point. Write a new frame that references the old one. |
| Passing `--approved` because the run asked for it | `--approved` records that a *person* authorized the change. Ask first. |
| Deleting an earned constraint that no longer applies | Update its `status` to `retired` or `superseded`; deletion erases why it existed. |
| Treating exit 5 as failure | It means the policy governs the resource but no store implements it yet. Report it as an explicit gap. |
| Adding a store without adding the resource to the policy | Unknown resources are denied by default, so the store would never be reached. |

## Related

- [pmcro-laws](../pmcro-laws/SKILL.md) - the laws view of this interface
- [pmcro-frames](../pmcro-frames/SKILL.md) - the frames view, including why they are immutable
- [Runtime boundary](../pmcro-orchestrator/references/runtime-boundary.md) - dispatch, queue, ingress, preflight
