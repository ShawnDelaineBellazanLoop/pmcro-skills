#!/usr/bin/env python3
"""Turn an inbound webhook payload into a queued, typed SeedIntent.

Ingress is the one place untrusted text enters the control plane, so it does
three things and nothing else: bound the payload, translate it into a SeedIntent
that matches the contract, and enqueue a PhaseMessage for the Orchestrator to
gate. It never dispatches, because an outside caller must not be able to start a
cycle by calling an endpoint (LAW-008).

An untrusted origin therefore produces a message marked requires_approval. Listing
an origin in trusted_ingress_sources is the deliberate act that removes that gate,
and it is a governance change, not a runtime convenience.

Webhook senders retry. The idempotency key is derived from the delivery id and
the payload bytes, so a retried delivery collapses into the first one at the
dispatcher (ARCH-007).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pmcro_runtime as rt  # noqa: E402
import queue_adapter as queue  # noqa: E402

DEFAULT_INTENT_FIELDS = ("intent", "text", "body", "message", "title")


def extract_intent(payload: dict, field: str | None = None) -> str | None:
    if field:
        value = payload.get(field)
        return value.strip() if isinstance(value, str) and value.strip() else None
    for candidate in DEFAULT_INTENT_FIELDS:
        value = payload.get(candidate)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def is_trusted(root: pathlib.Path, origin: str) -> bool:
    return origin in rt.load_config(root).get("trusted_ingress_sources", [])


def accept(
    root: pathlib.Path,
    payload: dict,
    *,
    origin: str,
    delivery_id: str,
    intent_field: str | None = None,
) -> dict:
    """Bound, translate, and enqueue. Returns the operator-facing outcome."""
    raw = rt.canonical_bytes(payload)
    max_bytes = int(rt.load_config(root).get("max_ingress_bytes", 65536))
    if len(raw) > max_bytes:
        return {"status": "refused", "reason": "payload-too-large", "bytes": len(raw), "limit": max_bytes}

    intent = extract_intent(payload, intent_field)
    if not intent:
        return {"status": "refused", "reason": "no-intent-field", "looked_for": list(DEFAULT_INTENT_FIELDS)}

    digest = hashlib.sha256(delivery_id.encode("utf-8") + b"|" + raw).hexdigest()
    short = digest[:12]
    trusted = is_trusted(root, origin)

    seed = {
        "type": "SeedIntent",
        "source": "webhook",
        "intent": intent,
        "constraints": [f"origin:{origin}", "trusted" if trusted else "untrusted-origin"],
        "strategy_hint": payload.get("strategy_hint") if isinstance(payload.get("strategy_hint"), str) else None,
        "evidence_refs": [f".pmcro/queue/seeds/seed-{short}.payload.json"],
        # An outside caller does not get to assert how sure we are about its
        # meaning; O-Mode raises confidence only after excavation.
        "confidence": "low",
    }
    errors = rt.validate_against(root, seed, "seed-intent.schema.json")
    if errors:
        return {"status": "refused", "reason": "seed-contract-violation", "errors": errors}

    seeds = root / rt.CONTROL_PLANE / "queue" / "seeds"
    rt.write_json(seeds / f"seed-{short}.payload.json", payload)
    seed_ref = f".pmcro/queue/seeds/seed-{short}.json"
    rt.write_json(root / seed_ref, seed)

    message = {
        "type": "PhaseMessage",
        "message_id": f"msg-ingress-{short}",
        "cycle_id": f"cyc-ingress-{short}",
        "source": "system",
        "target": "planner",
        "message_type": "seed-intent",
        "payload_ref": seed_ref,
        "idempotency_key": f"ingress:{digest}",
        "attempt": 1,
        "requires_approval": not trusted,
    }
    queued = queue.enqueue(root, message, origin=origin)
    return {"status": queued["status"], "seed_ref": seed_ref, "requires_approval": not trusted, **queued}


def main() -> int:
    parser = argparse.ArgumentParser(description="Accept a webhook payload as a queued SeedIntent.")
    parser.add_argument("payload", help="path to the inbound JSON payload, or - for stdin")
    parser.add_argument("--origin", required=True, help="identifier for the sending system, e.g. github:pmcro-skills")
    parser.add_argument("--delivery-id", required=True, help="the sender's delivery identifier, used for replay collapse")
    parser.add_argument("--intent-field", default=None, help="payload field holding the intent text")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    text = sys.stdin.read() if args.payload == "-" else pathlib.Path(args.payload).read_text(encoding="utf-8")
    start = pathlib.Path(__file__) if args.payload == "-" else pathlib.Path(args.payload)
    root = pathlib.Path(args.root).resolve() if args.root else rt.find_root(start)

    result = accept(
        root,
        json.loads(text),
        origin=args.origin,
        delivery_id=args.delivery_id,
        intent_field=args.intent_field,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "queued" else 1


if __name__ == "__main__":
    raise SystemExit(main())
