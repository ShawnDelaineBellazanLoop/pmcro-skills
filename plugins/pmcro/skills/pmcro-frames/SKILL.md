---
name: pmcro-frames
description: "Record and read PMCRO TrailFrames, and handle the common request to fix one. USE FOR: 'record a frame for this phase', 'show me the frames for cycle X', 'correct that frame', 'delete the bad frame', 'why can't I edit the trail', or any attempt to revise recorded history. Reach for it whenever a frame is being written, read, or questioned. DO NOT USE FOR: trail events (use pmcro-resource with events), checkpoints, or laws and constraints (use pmcro-laws or pmcro-resource)."
license: MIT
compatibility: "Requires Python 3.11+ and a .pmcro control plane. Delegates to pmcro-resource; standard library only."
metadata:
  protocol: pmcro
  tool_authority: orchestrator-only
---

# PMCRO frames

A TrailFrame is what a phase recorded: plan, artifact, check, reflection, or
decision, with the evidence it rests on. Frames can be created and read. They
cannot be updated or deleted, and that refusal is the feature - a trail that can
be revised after the fact proves nothing about what happened.

## When to use

- Recording a phase outcome as a frame.
- Listing the frames in a cycle, or reading one.
- Answering a request to correct or remove a frame.

## When not to use

- Trail events (`events`), checkpoints, laws, or constraints: `pmcro-resource`.
- Delivering messages between phases: the dispatcher in
  [runtime boundary](../pmcro-orchestrator/references/runtime-boundary.md).

## Workflow

### Record a frame

```bash
python .pmcro/scripts/resource_ops.py frames create --file frame.json
```

The payload is validated against `.pmcro/schemas/trail-frame.schema.json` before
anything is written. Exit 1 lists the offending fields; the frame is not partly
written on failure.

Required: `type`, `frame_id`, `cycle_id`, `phase`, `frame_type`, `summary`,
`created_utc`. `frame_type` is one of `intent`, `goal`, `research`, `plan`,
`tool-request`, `tool-result`, `artifact`, `check`, `reflection`, `decision`,
`handoff`.

Write the summary so it still makes sense to someone who was not in the session:
what was done, what it rests on, and what remains. A summary that reads "done"
is a frame that records nothing.

### Read frames

```bash
python .pmcro/scripts/resource_ops.py frames read
python .pmcro/scripts/resource_ops.py frames read --id frame-maf-host-20260915-checker
```

### When someone asks to fix a frame

Update and delete both return exit 2 with the reason naming LAW-010. The correct
response is not to edit the file directly; it is to record a new frame that
references the wrong one:

```json
{
  "type": "TrailFrame",
  "frame_id": "frame-<cycle>-correction-001",
  "cycle_id": "<same cycle>",
  "phase": "<phase making the correction>",
  "frame_type": "reflection",
  "summary": "Corrects frame-<id>: <what was wrong, and what is actually true>.",
  "source_refs": [".pmcro/trails/frames/<wrong-frame>.json"],
  "created_utc": "<now>"
}
```

The wrong frame stays. Two frames and a stated correction is a more honest
record than one frame that was quietly made right.

### Legacy frames

Six frames predate the current contract and are listed in
`.pmcro/trails/legacy-frames.json`. Verification reports them as LEGACY rather
than failing. Do not "fix" them to validate - that is the same rewrite LAW-010
forbids, with extra steps.

## Validation

- [ ] A created frame validates against the TrailFrame contract
- [ ] A correction was recorded as a new frame, not an edit
- [ ] `python .pmcro/tests/run_all.py` still reports all frames valid

## Common pitfalls

| Pitfall | Instead |
|---------|---------|
| Editing a frame file after the refusal | Record a correction frame that references it |
| Summaries like "completed successfully" | State what was produced and what it rests on |
| Inventing `evidence_refs` that do not exist | Reference real paths; a missing reference is worse than none |
| Adding fields the schema forbids | Phase payload belongs in the referenced artifact, not the frame |

## Related

- [pmcro-resource](../pmcro-resource/SKILL.md) - the generic interface
- [pmcro-laws](../pmcro-laws/SKILL.md) - LAW-010 in full
