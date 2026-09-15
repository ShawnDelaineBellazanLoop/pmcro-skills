#!/usr/bin/env python3
"""Shared PMCRO runtime helpers: schema checks, hashing, ledgers, trail writes.

Phase agents do not import this module. Only the Orchestrator boundary - the
dispatcher, the ingress adapter, and the queue adapter - executes it, because
operational tool authority belongs to the Orchestrator alone (docs/architecture.md).

The JSON Schema support here is a deliberate subset (type, const, enum,
required, properties, additionalProperties, items, minLength, minimum). The
repository contracts use only that subset, and a stdlib-only checker keeps the
control plane runnable on a machine with no third-party packages installed.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone

CONTROL_PLANE = ".pmcro"

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def utc_now() -> str:
    """Timestamp used for frames and events; second precision keeps trails diffable."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_root(start: pathlib.Path | None = None) -> pathlib.Path:
    """Walk upward to the repository that owns the .pmcro control plane."""
    here = (start or pathlib.Path(__file__)).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / CONTROL_PLANE).is_dir():
            return candidate
    raise SystemExit(f"ERROR: no {CONTROL_PLANE} control plane found above {here}")


def load_json(path: pathlib.Path | str):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def canonical_bytes(payload) -> bytes:
    """Stable byte form so a hash of the same content is the same hash anywhere."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_of(payload) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def write_json(path: pathlib.Path | str, payload) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def validate_instance(instance, schema, path: str = "$") -> list[str]:
    """Return a list of human-readable contract violations; empty means valid.

    Errors are collected rather than raised on the first problem so a caller can
    show an operator everything wrong with one envelope instead of one item at a
    time.
    """
    errors: list[str] = []

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']}")

    declared = schema.get("type")
    if declared is not None:
        names = declared if isinstance(declared, list) else [declared]
        if not _matches_type(instance, names):
            errors.append(f"{path}: expected type {declared}, got {type(instance).__name__}")
            return errors

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: does not match pattern {schema['pattern']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")

    if isinstance(instance, dict):
        errors.extend(_validate_object(instance, schema, path))

    if isinstance(instance, list) and "items" in schema:
        for index, item in enumerate(instance):
            errors.extend(validate_instance(item, schema["items"], f"{path}[{index}]"))

    return errors


def _matches_type(instance, names: list[str]) -> bool:
    for name in names:
        if name == "integer":
            if isinstance(instance, int) and not isinstance(instance, bool):
                return True
            continue
        if name == "number" and isinstance(instance, bool):
            continue
        expected = _TYPES.get(name)
        if expected is not None and isinstance(instance, expected):
            return True
    return False


def _validate_object(instance: dict, schema: dict, path: str) -> list[str]:
    errors: list[str] = []
    properties = schema.get("properties", {})

    for key in schema.get("required", []):
        if key not in instance:
            errors.append(f"{path}: missing required field '{key}'")

    if schema.get("additionalProperties") is False:
        for key in instance:
            if key not in properties:
                errors.append(f"{path}: unexpected field '{key}'")

    for key, value in instance.items():
        if key in properties:
            errors.extend(validate_instance(value, properties[key], f"{path}.{key}"))

    return errors


def validate_against(root: pathlib.Path, instance, schema_name: str) -> list[str]:
    """Validate an instance against a named schema in .pmcro/schemas."""
    schema_path = root / CONTROL_PLANE / "schemas" / schema_name
    return validate_instance(instance, load_json(schema_path))


def load_config(root: pathlib.Path) -> dict:
    """Runtime limits come from the control plane, never from a caller argument.

    A limit a caller could pass in is a limit a caller could raise, which is how
    bounded autonomy (LAW-007) quietly stops being bounded.
    """
    return load_json(root / CONTROL_PLANE / "templates" / "pmcro.config.json")


def trail_path(root: pathlib.Path) -> pathlib.Path:
    config = load_config(root)
    return root / config.get("trail_path", ".pmcro/trails/events.jsonl")


def next_event_id(root: pathlib.Path) -> str:
    """Continue the evt-NNN sequence already present in the trail."""
    path = trail_path(root)
    highest = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            match = re.match(r"^\{.*\"event_id\"\s*:\s*\"evt-(\d+)\"", line)
            if match:
                highest = max(highest, int(match.group(1)))
    return f"evt-{highest + 1:03d}"


def append_event(root: pathlib.Path, event: dict) -> dict:
    """Append-only trail write (LAW-010). Corrections are new events, never edits."""
    path = trail_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event) + "\n")
    return event


def ledger_path(root: pathlib.Path) -> pathlib.Path:
    return root / CONTROL_PLANE / "trails" / "dispatch-ledger.json"


def load_ledger(root: pathlib.Path) -> dict:
    path = ledger_path(root)
    if path.exists():
        return load_json(path)
    return {"version": 1, "dispatches": []}


def save_ledger(root: pathlib.Path, ledger: dict) -> pathlib.Path:
    return write_json(ledger_path(root), ledger)


def find_by_idempotency_key(ledger: dict, key: str) -> dict | None:
    """At-least-once transports redeliver; the ledger is what makes replay harmless."""
    if not key:
        return None
    for entry in ledger.get("dispatches", []):
        if entry.get("idempotency_key") == key:
            return entry
    return None


def cycle_entries(ledger: dict, cycle_id: str) -> list[dict]:
    return [e for e in ledger.get("dispatches", []) if e.get("cycle_id") == cycle_id]


def attempts_for(ledger: dict, cycle_id: str, target: str) -> int:
    return len([e for e in cycle_entries(ledger, cycle_id) if e.get("target") == target])


def last_frame_hash(ledger: dict) -> str | None:
    dispatches = ledger.get("dispatches", [])
    return dispatches[-1].get("payload_sha256") if dispatches else None
