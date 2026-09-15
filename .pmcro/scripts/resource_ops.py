#!/usr/bin/env python3
"""Generic CRUD over PMCRO control-plane resources, gated by one policy table.

The operations are the same four everywhere - create, read, update, delete - so
the interesting part is not the verbs but which verbs a resource refuses. A frame
cannot be updated or deleted because the trail would stop being evidence; a law
can be read by anyone but changed only with review. Writing that table once, in
.pmcro/policies/resource-operations.json, means an editor, an agent, and the .NET
runtime all get the same answer instead of three implementations drifting apart.

Every decision is one of three:

  allow     - proceed
  approval  - legitimate, but a human authorizes it first (LAW-008)
  deny      - never valid here; the reason names the law that forbids it

Exit codes: 0 done, 1 contract or input error, 2 denied by policy, 3 not found,
4 approval required, 5 policy declares the resource but no store implements it.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pmcro_runtime as rt  # noqa: E402

OPERATIONS = ("create", "read", "update", "delete")

EXIT_OK = 0
EXIT_INPUT = 1
EXIT_DENIED = 2
EXIT_NOT_FOUND = 3
EXIT_APPROVAL = 4
EXIT_NOT_IMPLEMENTED = 5

POLICY_PATH = "policies/resource-operations.json"


def load_policy(root: pathlib.Path) -> dict:
    return rt.load_json(root / rt.CONTROL_PLANE / POLICY_PATH)


def decide(policy: dict, resource: str, operation: str) -> tuple[str, str]:
    """Return (decision, reason). Unknown resources and operations are denied.

    Defaulting to deny matters more than it looks: a resource someone forgot to
    add to the table should refuse the operation, not inherit a permissive
    default and quietly allow a delete.
    """
    if operation not in OPERATIONS:
        return "deny", f"'{operation}' is not a CRUD operation; expected one of {list(OPERATIONS)}"

    entry = policy.get("resources", {}).get(resource)
    if entry is None:
        known = sorted(policy.get("resources", {}))
        return "deny", f"unknown resource '{resource}'; policy covers {known}"

    rule = entry.get(operation)
    if not isinstance(rule, dict) or "decision" not in rule:
        return "deny", f"policy declares no decision for {resource}.{operation}"

    return rule["decision"], rule.get("reason", "")


def policy_table(policy: dict) -> list[dict]:
    """The whole matrix, for an agent or a human who wants to see the rules."""
    rows = []
    for name, entry in sorted(policy.get("resources", {}).items()):
        row = {"resource": name, "summary": entry.get("summary", ""), "path": entry.get("path", "")}
        for operation in OPERATIONS:
            rule = entry.get(operation, {})
            row[operation] = rule.get("decision", "deny")
        rows.append(row)
    return rows


LAW_HEADING = re.compile(r"^##\s+(LAW-\d+):\s*(.+)$")


def _laws_file(root: pathlib.Path) -> pathlib.Path:
    return root / rt.CONTROL_PLANE / "laws" / "constitution.md"


def parse_laws(text: str) -> list[dict]:
    """Read the constitution into records without making the prose the loser.

    The markdown stays the human-readable source; this turns it into the list an
    agent can actually work with, so there is no second copy of the laws to drift.
    """
    laws: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        match = LAW_HEADING.match(line.strip())
        if match:
            current = {"id": match.group(1), "title": match.group(2).strip(), "rule": ""}
            laws.append(current)
        elif current is not None and line.strip():
            current["rule"] = (current["rule"] + " " + line.strip()).strip()
    return laws


def laws_store(root: pathlib.Path, operation: str, identifier: str | None, payload: dict | None) -> tuple[int, dict]:
    path = _laws_file(root)
    text = path.read_text(encoding="utf-8")
    laws = parse_laws(text)

    if operation == "read":
        if identifier is None:
            return EXIT_OK, {"resource": "laws", "count": len(laws), "laws": laws}
        found = next((law for law in laws if law["id"] == identifier), None)
        if found is None:
            return EXIT_NOT_FOUND, {"error": f"no law '{identifier}'", "known": [law['id'] for law in laws]}
        return EXIT_OK, {"resource": "laws", "law": found}

    if operation == "create":
        if not payload or not payload.get("id") or not payload.get("title") or not payload.get("rule"):
            return EXIT_INPUT, {"error": "a law needs id, title, and rule"}
        if any(law["id"] == payload["id"] for law in laws):
            return EXIT_INPUT, {"error": f"law '{payload['id']}' already exists; update it instead"}
        section = f"\n## {payload['id']}: {payload['title']}\n\n{payload['rule']}\n"
        path.write_text(text.rstrip("\n") + "\n" + section, encoding="utf-8")
        return EXIT_OK, {"resource": "laws", "created": payload["id"]}

    if operation == "update":
        if identifier is None or not payload or not payload.get("rule"):
            return EXIT_INPUT, {"error": "update needs --id and a payload with a rule"}
        target = next((law for law in laws if law["id"] == identifier), None)
        if target is None:
            return EXIT_NOT_FOUND, {"error": f"no law '{identifier}'"}
        old_block = f"## {target['id']}: {target['title']}\n\n{target['rule']}"
        if old_block not in text:
            return EXIT_INPUT, {"error": f"could not locate the exact block for '{identifier}'; edit the file directly"}
        title = payload.get("title", target["title"])
        path.write_text(text.replace(old_block, f"## {identifier}: {title}\n\n{payload['rule']}"), encoding="utf-8")
        return EXIT_OK, {"resource": "laws", "updated": identifier}

    return EXIT_INPUT, {"error": f"laws does not implement '{operation}'"}


def constraints_store(root: pathlib.Path, operation: str, identifier: str | None, payload: dict | None) -> tuple[int, dict]:
    path = root / rt.CONTROL_PLANE / "trails" / "constraints" / "earned-constraints.json"
    document = rt.load_json(path)
    constraints = document.get("constraints", [])

    if operation == "read":
        if identifier is None:
            return EXIT_OK, {"resource": "constraints", "count": len(constraints), "constraints": constraints}
        found = next((c for c in constraints if c.get("id") == identifier), None)
        if found is None:
            return EXIT_NOT_FOUND, {"error": f"no constraint '{identifier}'"}
        return EXIT_OK, {"resource": "constraints", "constraint": found}

    if operation == "create":
        if not payload or not payload.get("id") or not payload.get("rule"):
            return EXIT_INPUT, {"error": "a constraint needs at least id and rule"}
        if any(c.get("id") == payload["id"] for c in constraints):
            return EXIT_INPUT, {"error": f"constraint '{payload['id']}' already exists"}
        constraints.append(payload)
        rt.write_json(path, document)
        return EXIT_OK, {"resource": "constraints", "created": payload["id"]}

    if operation == "update":
        if identifier is None or not payload:
            return EXIT_INPUT, {"error": "update needs --id and a payload"}
        for index, constraint in enumerate(constraints):
            if constraint.get("id") == identifier:
                constraints[index] = {**constraint, **payload, "id": identifier}
                rt.write_json(path, document)
                return EXIT_OK, {"resource": "constraints", "updated": identifier, "constraint": constraints[index]}
        return EXIT_NOT_FOUND, {"error": f"no constraint '{identifier}'"}

    return EXIT_INPUT, {"error": f"constraints does not implement '{operation}'"}


def _json_directory_store(
    root: pathlib.Path,
    resource: str,
    directory: pathlib.Path,
    id_field: str,
    id_prefix: str,
    schema: str,
    operation: str,
    identifier: str | None,
    payload: dict | None,
) -> tuple[int, dict]:
    """Shared behavior for resources kept as one JSON document per record."""
    directory.mkdir(parents=True, exist_ok=True)
    records = {}
    for path in sorted(directory.glob("*.json")):
        try:
            document = rt.load_json(path)
        except json.JSONDecodeError:
            continue
        records[document.get(id_field, path.stem)] = (path, document)

    if operation == "read":
        if identifier is None:
            return EXIT_OK, {
                "resource": resource,
                "count": len(records),
                "ids": sorted(records),
            }
        if identifier not in records:
            return EXIT_NOT_FOUND, {"error": f"no {resource} record '{identifier}'"}
        return EXIT_OK, {"resource": resource, id_field: identifier, "record": records[identifier][1]}

    if operation == "create":
        if not payload or not payload.get(id_field):
            return EXIT_INPUT, {"error": f"a {resource} record needs {id_field}"}
        record_id = payload[id_field]
        if record_id in records:
            return EXIT_INPUT, {"error": f"{record_id} already exists"}
        errors = rt.validate_against(root, payload, schema)
        if errors:
            return EXIT_INPUT, {"error": f"{resource} contract violation", "errors": errors}
        filename = record_id.removeprefix(id_prefix) + ".json"
        rt.write_json(directory / filename, payload)
        return EXIT_OK, {"resource": resource, "created": record_id, "path": str((directory / filename).relative_to(root)).replace("\\", "/")}

    if operation == "update":
        if identifier is None or not payload:
            return EXIT_INPUT, {"error": "update needs --id and a payload"}
        if identifier not in records:
            return EXIT_NOT_FOUND, {"error": f"no {resource} record '{identifier}'"}
        path, document = records[identifier]
        merged = {**document, **payload, id_field: identifier}
        errors = rt.validate_against(root, merged, schema)
        if errors:
            return EXIT_INPUT, {"error": f"{resource} contract violation", "errors": errors}
        rt.write_json(path, merged)
        return EXIT_OK, {"resource": resource, "updated": identifier}

    return EXIT_INPUT, {"error": f"{resource} does not implement '{operation}'"}


def frames_store(root: pathlib.Path, operation: str, identifier: str | None, payload: dict | None) -> tuple[int, dict]:
    return _json_directory_store(
        root, "frames", root / rt.CONTROL_PLANE / "trails" / "frames",
        "frame_id", "frame-", "trail-frame.schema.json", operation, identifier, payload,
    )


def checkpoints_store(root: pathlib.Path, operation: str, identifier: str | None, payload: dict | None) -> tuple[int, dict]:
    return _json_directory_store(
        root, "checkpoints", root / rt.CONTROL_PLANE / "checkpoints",
        "checkpoint_id", "checkpoint-", "checkpoint.schema.json", operation, identifier, payload,
    )


def events_store(root: pathlib.Path, operation: str, identifier: str | None, payload: dict | None) -> tuple[int, dict]:
    path = rt.trail_path(root)

    if operation == "read":
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        events = [json.loads(line) for line in lines if line.strip()]
        if identifier is not None:
            events = [e for e in events if e.get("cycle_id") == identifier or e.get("event_id") == identifier]
            if not events:
                return EXIT_NOT_FOUND, {"error": f"no events for '{identifier}'"}
        return EXIT_OK, {"resource": "events", "count": len(events), "events": events}

    if operation == "create":
        if not payload or not payload.get("summary") or not payload.get("cycle_id"):
            return EXIT_INPUT, {"error": "an event needs at least cycle_id and summary"}
        event = {
            "event_id": payload.get("event_id") or rt.next_event_id(root),
            "cycle_id": payload["cycle_id"],
            "phase": payload.get("phase", "system"),
            "event_type": payload.get("event_type", "resource-operation"),
            "summary": payload["summary"],
            "evidence_refs": payload.get("evidence_refs", []),
        }
        rt.append_event(root, event)
        return EXIT_OK, {"resource": "events", "created": event["event_id"]}

    return EXIT_INPUT, {"error": f"events does not implement '{operation}'"}


STORES = {
    "laws": laws_store,
    "constraints": constraints_store,
    "frames": frames_store,
    "checkpoints": checkpoints_store,
    "events": events_store,
}


def run(
    root: pathlib.Path,
    resource: str,
    operation: str,
    identifier: str | None = None,
    payload: dict | None = None,
    approved: bool = False,
    record_evidence: bool = True,
) -> tuple[int, dict]:
    """Decide first, act second. The decision is part of the result either way."""
    policy = load_policy(root)
    decision, reason = decide(policy, resource, operation)
    envelope = {"resource": resource, "operation": operation, "decision": decision}
    if reason:
        envelope["reason"] = reason

    if decision == "deny":
        return EXIT_DENIED, {**envelope, "status": "denied"}

    if decision == "approval" and not approved:
        return EXIT_APPROVAL, {
            **envelope,
            "status": "approval-required",
            "note": "re-run with --approved once a human has authorized this change",
        }

    store = STORES.get(resource)
    if store is None:
        return EXIT_NOT_IMPLEMENTED, {
            **envelope,
            "status": "not-implemented",
            "note": f"policy governs '{resource}' but no store implements it yet; use the files directly and add a store before relying on this path",
        }

    code, result = store(root, operation, identifier, payload)
    outcome = {**envelope, "status": "done" if code == EXIT_OK else "failed", **result}

    # A mutation that leaves no trace is indistinguishable from one that never
    # happened, so a successful change records itself before returning.
    if code == EXIT_OK and operation != "read" and record_evidence and resource != "events":
        rt.append_event(root, {
            "event_id": rt.next_event_id(root),
            "cycle_id": (payload or {}).get("cycle_id", "cyc-resource-ops"),
            "phase": "orchestrator",
            "event_type": f"{resource}-{operation}",
            "summary": f"{operation} on {resource}"
                       + (f" '{identifier or (payload or {}).get('id') or ''}'" if operation != "read" else "")
                       + (" (human-approved)" if approved and decision == "approval" else ""),
            "evidence_refs": [policy.get("resources", {}).get(resource, {}).get("path", "")],
        })

    return code, outcome


def main() -> int:
    parser = argparse.ArgumentParser(description="CRUD a PMCRO control-plane resource under policy.")
    parser.add_argument("resource", help="laws, constraints, frames, events, checkpoints, ... or 'policy' to print the matrix")
    parser.add_argument("operation", nargs="?", default="read", choices=[*OPERATIONS, "policy"])
    parser.add_argument("--id", dest="identifier", default=None, help="record id; omit on read to list")
    parser.add_argument("--file", default=None, help="JSON payload file for create or update")
    parser.add_argument("--data", default=None, help="inline JSON payload for create or update")
    parser.add_argument("--approved", action="store_true", help="a human authorized an approval-gated operation")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve() if args.root else rt.find_root(pathlib.Path(__file__))

    if args.resource == "policy" or args.operation == "policy":
        print(json.dumps({"policy": policy_table(load_policy(root))}, indent=2))
        return EXIT_OK

    payload = None
    if args.file:
        payload = rt.load_json(args.file)
    elif args.data:
        try:
            payload = json.loads(args.data)
        except json.JSONDecodeError as error:
            print(json.dumps({"status": "failed", "error": f"--data is not valid JSON: {error}"}, indent=2))
            return EXIT_INPUT

    code, result = run(root, args.resource, args.operation, args.identifier, payload, approved=args.approved)
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
