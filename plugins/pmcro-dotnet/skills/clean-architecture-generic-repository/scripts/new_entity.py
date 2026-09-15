#!/usr/bin/env python3
"""Generate the entity, its repository interface, and its repository from a spec.

The division of labour this script exists to enforce: a model turns intent into a
validated spec, and this turns the spec into code. Neither half asks the model to
be right about C# it cannot check.

That matters most for a small local model. A frontier model will improvise four
correct files from a one-line SKILL.md and make this look unnecessary; an 8B model
will produce something that looks like C# and does not compile, and will not say
so. The spec is small enough for it to fill reliably and structured enough to be
rejected when it is wrong.

Usage:
  python new_entity.py <spec.json> --domain <dir> --infrastructure <dir> [--force]
  python new_entity.py <spec.json> --check      (validate the spec, write nothing)

Exit codes: 0 written, 1 invalid spec, 2 refused to overwrite, 3 unknown resource.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_EXISTS = 2
EXIT_UNKNOWN_RESOURCE = 3

ALLOWED_TYPES = {
    "string": "string",
    "int": "int",
    "long": "long",
    "decimal": "decimal",
    "bool": "bool",
    "Guid": "Guid",
    "DateTimeOffset": "DateTimeOffset",
    "string[]": "IList<string>",
    "int[]": "IList<int>",
}

DEFAULTS = {
    "string": ' = string.Empty;',
    "string[]": " = [];",
    "int[]": " = [];",
}


def validate(spec: dict, policy: dict | None) -> list[str]:
    """Structural checks first, then the one semantic check that matters."""
    errors: list[str] = []
    metadata = spec.get("metadata") or {}
    body = spec.get("spec") or {}

    if spec.get("kind") != "EntityScaffoldSpec":
        errors.append("kind must be EntityScaffoldSpec")

    name = metadata.get("name", "")
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", name):
        errors.append(f"metadata.name '{name}' must be PascalCase and singular")

    resource = metadata.get("resource", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", resource):
        errors.append(f"metadata.resource '{resource}' must be kebab-case")

    if len(metadata.get("summary", "")) < 20:
        errors.append("metadata.summary must be a real sentence, not a label")

    properties = body.get("properties") or []
    if not properties:
        errors.append("spec.properties must list at least one property")

    seen = set()
    for index, prop in enumerate(properties):
        prop_name = prop.get("name", "")
        if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", prop_name):
            errors.append(f"spec.properties[{index}].name '{prop_name}' must be PascalCase")
        if prop_name in seen:
            errors.append(f"spec.properties[{index}].name '{prop_name}' is duplicated")
        seen.add(prop_name)
        if prop.get("type") not in ALLOWED_TYPES:
            errors.append(f"spec.properties[{index}].type '{prop.get('type')}' is not one of {sorted(ALLOWED_TYPES)}")

    natural_key = body.get("naturalKey")
    if natural_key and natural_key not in seen:
        errors.append(f"spec.naturalKey '{natural_key}' is not one of the declared properties")

    # The check worth having: a resource the policy does not know produces code that
    # compiles and is denied at runtime. Catching it here turns a confusing failure
    # into a clear one.
    if policy is not None and resource and resource not in policy.get("resources", {}):
        errors.append(
            f"metadata.resource '{resource}' is not in the policy table; add it to "
            f".pmcro/policies/resource-operations.json first, or the repository will be denied every verb"
        )

    return errors


def render_entity(spec: dict) -> str:
    metadata, body = spec["metadata"], spec["spec"]
    name, resource = metadata["name"], metadata["resource"]
    lines = [
        "using ProjectName.Domain.Common;",
        "",
        "namespace ProjectName.Domain.Entities;",
        "",
        "/// <summary>",
        f"/// {metadata['summary']}",
        "/// </summary>",
        "/// <remarks>",
        f'/// Governed as <c>{resource}</c>. Which verbs that permits is decided by the policy',
        "/// table, not by anything in this file - the attribute is the whole declaration.",
        "/// </remarks>",
        f'[GovernedResource("{resource}")]',
        f"public sealed class {name} : BaseEntity",
        "{",
    ]

    for index, prop in enumerate(body["properties"]):
        if index:
            lines.append("")
        summary = prop.get("summary") or f"{prop['name']}."
        declared = ALLOWED_TYPES[prop["type"]]
        initializer = DEFAULTS.get(prop["type"], "")
        accessor = "get; init;" if prop["type"].endswith("[]") else "get; set;"
        lines.append(f"    /// <summary>{summary}</summary>")
        lines.append(f"    public {declared} {prop['name']} {{ {accessor} }}{initializer}")

    lines.append("}")
    lines.append("")
    lines.append("/// <summary>The repository for <see cref=\"" + name + "\"/>.</summary>")
    lines.append("/// <remarks>")
    lines.append("/// Empty because the generic base supplies every verb and the policy table supplies")
    lines.append("/// the refusals. Add a member here only when this model needs something beyond CRUD.")
    lines.append("/// </remarks>")
    lines.append(f"public interface I{name}Repository : IGenericRepository<{name}>;")
    lines.append("")
    return "\n".join(lines)


def render_repository(spec: dict) -> str:
    name = spec["metadata"]["name"]
    return f"""using ProjectName.Domain.Entities;
using ProjectName.Domain.Policy;

namespace ProjectName.Infrastructure.Repositories;

/// <summary>{name} records, stored as JSON.</summary>
/// <param name="filePath">Where the collection is stored.</param>
/// <param name="policy">The control-plane table.</param>
/// <param name="approvals">Who has authorized what in this session.</param>
public sealed class {name}Repository(string filePath, ResourceOperationPolicy policy, IApprovalContext approvals)
    : JsonFileRepository<{name}>(filePath, policy, approvals), I{name}Repository;
"""


def find_policy(start: pathlib.Path) -> dict | None:
    """Locate the control-plane policy by walking up, so the script works from anywhere."""
    for candidate in [start, *start.parents]:
        path = candidate / ".pmcro" / "policies" / "resource-operations.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def write(path: pathlib.Path, content: str, force: bool) -> bool:
    """Refuse to overwrite by default; a generator that clobbers hand edits is a liability."""
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold an entity and its repository from a spec.")
    parser.add_argument("spec", help="path to an EntityScaffoldSpec JSON file")
    parser.add_argument("--domain", help="directory for Entities (…/ProjectName.Domain/Entities)")
    parser.add_argument("--infrastructure", help="directory for repositories (…/ProjectName.Infrastructure/Repositories)")
    parser.add_argument("--check", action="store_true", help="validate the spec and write nothing")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args()

    spec_path = pathlib.Path(args.spec).resolve()
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid", "errors": [f"could not read spec: {error}"]}, indent=2))
        return EXIT_INVALID

    policy = find_policy(pathlib.Path(args.domain).resolve() if args.domain else spec_path.parent)
    errors = validate(spec, policy)
    if errors:
        unknown = any("not in the policy table" in e for e in errors)
        print(json.dumps({"status": "invalid", "errors": errors}, indent=2))
        return EXIT_UNKNOWN_RESOURCE if unknown and len(errors) == 1 else EXIT_INVALID

    name = spec["metadata"]["name"]
    if args.check:
        print(json.dumps({"status": "valid", "entity": name, "resource": spec["metadata"]["resource"]}, indent=2))
        return EXIT_OK

    if not args.domain or not args.infrastructure:
        print(json.dumps({"status": "invalid", "errors": ["--domain and --infrastructure are required unless --check"]}, indent=2))
        return EXIT_INVALID

    targets = {
        pathlib.Path(args.domain).resolve() / f"{name}.cs": render_entity(spec),
        pathlib.Path(args.infrastructure).resolve() / f"{name}Repository.cs": render_repository(spec),
    }

    refused = [str(p) for p, c in targets.items() if not write(p, c, args.force)]
    if refused:
        print(json.dumps({"status": "refused", "existing": refused, "hint": "pass --force to overwrite"}, indent=2))
        return EXIT_EXISTS

    print(json.dumps({
        "status": "written",
        "entity": name,
        "resource": spec["metadata"]["resource"],
        "files": [str(p) for p in targets],
        "next": "add a named property to IUnitOfWork only if callers keep reaching for this type",
    }, indent=2))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
