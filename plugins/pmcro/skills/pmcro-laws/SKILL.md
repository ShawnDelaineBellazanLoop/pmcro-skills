---
name: pmcro-laws
description: "List, quote, and explain the PMCR-O constitutional laws, and handle requests to change them. USE FOR: 'what are the laws', 'show me LAW-010', 'which law says the trail is append-only', 'why was this rejected', 'add a law', 'change this law', or any question about what the framework forbids and why. Reach for it whenever a refusal needs to be explained by the rule behind it. DO NOT USE FOR: earned constraints, which have their own promotion lifecycle, or frames and events (use pmcro-resource or pmcro-frames)."
license: MIT
compatibility: "Requires Python 3.11+ and a .pmcro control plane. Delegates to pmcro-resource; standard library only."
metadata:
  protocol: pmcro
  tool_authority: orchestrator-only
---

# PMCRO laws

The laws are the rules the framework will not violate. They live as prose in
`.pmcro/laws/constitution.md` and are read as records through the generic
resource interface, so there is no second copy to drift.

## When to use

- Listing every law, or quoting one by id.
- Answering "which law forbids this?" after an operation was refused.
- Handling a request to add or reword a law.

## When not to use

- Earned constraints (`ARCH-###`): evidence-derived, with the promotion lifecycle
  in `.pmcro/laws/constraint-promotion.md`. Use `pmcro-resource` with `constraints`.
- Frames, events, checkpoints: use `pmcro-resource` or `pmcro-frames`.

## Workflow

### List every law

```bash
python .pmcro/scripts/resource_ops.py laws read
```

Returns `{id, title, rule}` per `LAW-###`. Quote the `rule` verbatim when
explaining a refusal - paraphrasing a law is how its meaning drifts.

### Quote one law

```bash
python .pmcro/scripts/resource_ops.py laws read --id LAW-010
```

Exit 3 means no such law; list them rather than guessing at the id.

### Change a law

Reading is `allow`. Creating or rewording is `approval`: laws are versioned and
changes require explicit review, so the run stops with exit 4 until a person
authorizes it.

```bash
python .pmcro/scripts/resource_ops.py laws update --id LAW-010 --data "{\"rule\":\"...\"}"
# exit 4: approval-required
python .pmcro/scripts/resource_ops.py laws update --id LAW-010 --data "{\"rule\":\"...\"}" --approved
```

Ask the person first and say what the change does. `--approved` records that a
human agreed, so passing it because the tool asked for it makes that record false.

### Deleting a law

Denied, always. A law that no longer applies is superseded by a reviewed
revision; deleting it erases the reason every downstream constraint exists.

## Validation

- [ ] Quoted law text matches `constitution.md` exactly
- [ ] No law changed without a person authorizing it in the conversation
- [ ] An approved change produced a trail event

## The laws at a glance

| Law | Subject |
|-----|---------|
| LAW-001 | Forward-only flow |
| LAW-002 | Ground truth over claims |
| LAW-003 | Minimal validated plan |
| LAW-004 | Complete artifacts |
| LAW-005 | Independent checking |
| LAW-006 | Reflection creates constraints |
| LAW-007 | Bounded autonomy |
| LAW-008 | Human veto |
| LAW-009 | Truthful completion |
| LAW-010 | Immutable trail |

A routing aid, not the source. Read the file for the text.

## Related

- [pmcro-resource](../pmcro-resource/SKILL.md) - the generic interface this delegates to
- [pmcro-frames](../pmcro-frames/SKILL.md) - LAW-010 in practice
