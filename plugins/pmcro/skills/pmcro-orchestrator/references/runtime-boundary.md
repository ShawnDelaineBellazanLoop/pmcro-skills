# Runtime boundary

The control scripts under `.pmcro/scripts/` are the Orchestrator's hands. Phase
agents never invoke them; they return typed messages and ToolIntents, and the
Orchestrator runs the scripts under policy.

Everything here is stdlib Python, so it runs on a machine with no package
installs available.

## Delivering a PhaseMessage

```bash
python .pmcro/scripts/dispatch_message.py <message.json> [--approved] [--checkpoint <file>]
```

Every delivery passes the same five gates, whatever transport carried the
message: envelope contract, forward-only routing, replay suppression by
`idempotency_key`, per-phase attempt bounds, and the approval hold. A delivered
message leaves a hash-chained handoff TrailFrame and one trail event.

Exit codes are the decision: `0` delivered or duplicate, `1` contract violation,
`2` routing violation, `3` attempt limit (ESCALATE), `4` approval required.

Re-entering planning means opening a new `cycle_id`. The dispatcher refuses an
`orchestrator -> planner` message that reuses a cycle that already has
dispatches, because attempt counters and the Trail both lose meaning otherwise.

## Queued delivery

```bash
python .pmcro/scripts/queue_adapter.py enqueue --message <message.json>
python .pmcro/scripts/queue_adapter.py drain [--approved]
python .pmcro/scripts/queue_adapter.py status
```

Jobs move through `pending → processing → done | held | dead`. A drain that dies
leaves an expired lease that the next drain reclaims, so delivery is at-least-once;
that is safe only because the dispatcher suppresses replays. The drain decides
nothing itself - it maps dispatcher exit codes to queue states, which keeps queue
behavior and cycle governance from drifting apart.

`held` is an approval hold, not a failure. `dead` needs a human: either a refusal
no retry can fix, or a message the Orchestrator kept refusing until the queue's
attempt cap.

## Webhook ingress

```bash
python .pmcro/scripts/ingress.py <payload.json> --origin <system> --delivery-id <id>
```

Ingress bounds the payload, extracts an intent, writes a SeedIntent at `low`
confidence, and enqueues a PhaseMessage. It never dispatches: an outside caller
must not be able to start a cycle by reaching an endpoint. Messages from an
origin outside `trusted_ingress_sources` carry `requires_approval`, and adding an
origin to that list is a governance change.

## Host preflight

```bash
python .pmcro/scripts/validate_host_boundary.py [--problems-only]
```

Checks what a MAF host adapter can be held to before any host exists: registry
contract, the declared `path_base` for resolving registry paths, containment
inside the plugin, envelope types resolving to `.pmcro/schemas`, MAF
discoverability of each `SKILL.md`, and tool-authority declarations. The report
also names what it cannot check - agent instantiation, MCP operations, and an
end-to-end cycle - so a green preflight is never mistaken for a working host.
