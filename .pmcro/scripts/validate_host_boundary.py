#!/usr/bin/env python3
"""Preflight the MAF host adapter and the Agent Skills MCP boundary.

A host adapter is handed paths from a registry and asked to instantiate agents.
Most of what can go wrong there is decidable before any model or host exists: a
path that escapes the plugin, a SKILL.md that is not discoverable, an envelope
type with no contract behind it, or a phase skill that quietly claims tool
authority. Checking those offline means a host integration fails for real reasons
rather than for bookkeeping ones (docs/maf-skill-discovery.md,
references/maf-agent-loading.md, docs/agent-skills-mcp.md).

What this cannot check is a live host: creating agents, calling a model, and
executing MCP tools need a running host and credentials. Those stay ESCALATE
until the host is configured, and this report says so rather than implying
coverage it does not have (LAW-009).

Exit codes: 0 all checks pass, 1 one or more failures.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pmcro_runtime as rt  # noqa: E402

# Envelope names an adapter may declare, and the contract each one must resolve to.
ENVELOPE_SCHEMAS = {
    "IntentEnvelope": "intent-envelope.schema.json",
    "PlanEnvelope": "plan-envelope.schema.json",
    "ArtifactEnvelope": "artifact-envelope.schema.json",
    "CheckReport": "check-report.schema.json",
    "ReflectionFrame": "reflection-frame.schema.json",
    "OrchestratorDecision": "orchestrator-decision.schema.json",
    "PlanningContext": "planning-context.schema.json",
    "PhaseMessage": "phase-message.schema.json",
    "ToolIntent": "tool-intent.schema.json",
    "ToolResult": "tool-result.schema.json",
}

AUTHORITY_SKILLS = {"orchestrator-agent", "pmcro-orchestrator", "agent-skills-operator"}

# Plugins this control plane governs. A vendored capability plugin is not held to
# the declaration rule - it plainly executes things - but it is reported, because
# an ungoverned capability sitting in the same tree is exactly what should be
# visible to whoever configures the host.
GOVERNED_PLUGINS = {"pmcro", "pmcro-csuite", "pmcro-skill-creator"}


def read_frontmatter(path: pathlib.Path) -> dict[str, str]:
    """Read the flat and one-level-nested keys a MAF provider cares about.

    A full YAML parser is not available in the stdlib and the frontmatter in this
    repository is deliberately simple, so a small reader keeps the control plane
    dependency-free (ARCH-008).
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---\n")
    block, _, _ = rest.partition("\n---")
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        fields[key.strip()] = value.strip().strip('"')
    return fields


def finding(check: str, status: str, detail: str, ref: str = "") -> dict:
    return {"check": check, "status": status, "detail": detail, "ref": ref}


def check_registry(root: pathlib.Path, registry_path: pathlib.Path) -> list[dict]:
    """Registry contract plus path safety: the adapter's first two obligations."""
    findings: list[dict] = []
    registry = rt.load_json(registry_path)
    # "Relative to the registry or plugin root" is two different answers, and an
    # adapter that picks the wrong one fails with a missing-file error that looks
    # like a packaging bug. The registry says which base it means; skill-root is
    # the default because that is what the shipped entries use.
    base_choice = registry.get("path_base", "skill-root")
    bases = {"registry": registry_path.parent, "skill-root": registry_path.parent.parent}
    base = bases.get(base_choice)
    if base is None:
        return [finding("registry-contract", "FAIL", f"unknown path_base '{base_choice}'", str(registry_path))]
    # <plugin>/skills/<skill>/assets/agents-index.json -> <plugin>
    plugin_root = registry_path.parents[3]

    for agent in registry.get("agents", []):
        for field in ("id", "phase", "skill", "definition", "input", "output"):
            if not agent.get(field):
                findings.append(finding("registry-contract", "FAIL", f"agent entry missing '{field}'", str(registry_path)))

        for field in ("skill", "definition"):
            raw = agent.get(field, "")
            if not raw:
                continue
            candidate = pathlib.Path(raw)
            if candidate.is_absolute():
                findings.append(finding("path-safety", "FAIL", f"{agent.get('id')} {field} is absolute", raw))
                continue
            resolved = (base / candidate).resolve()
            if plugin_root.resolve() not in resolved.parents:
                findings.append(finding("path-safety", "FAIL", f"{agent.get('id')} {field} escapes the plugin root", raw))
            elif not resolved.exists():
                findings.append(finding("path-safety", "FAIL", f"{agent.get('id')} {field} does not exist", raw))
            else:
                findings.append(finding("path-safety", "PASS", f"{agent.get('id')} {field} resolves inside the plugin", raw))
    return findings


def check_envelopes(root: pathlib.Path, registry_path: pathlib.Path) -> list[dict]:
    """Every declared envelope type must have a contract the adapter can validate against.

    An unmapped type is reported rather than ignored: it means the adapter would
    accept whatever an agent returned, which is how untyped state re-enters a
    typed system.
    """
    findings: list[dict] = []
    schemas = root / rt.CONTROL_PLANE / "schemas"
    for agent in rt.load_json(registry_path).get("agents", []):
        for direction in ("input", "output"):
            name = agent.get(direction, "")
            schema = ENVELOPE_SCHEMAS.get(name)
            if schema is None:
                findings.append(finding("envelope-mapping", "UNMAPPED", f"{agent.get('id')} {direction} '{name}' has no schema in .pmcro/schemas", name))
            elif not (schemas / schema).exists():
                findings.append(finding("envelope-mapping", "FAIL", f"{agent.get('id')} {direction} '{name}' maps to missing {schema}", schema))
            else:
                findings.append(finding("envelope-mapping", "PASS", f"{agent.get('id')} {direction} '{name}' resolves to {schema}", schema))
    return findings


def check_tool_authority(root: pathlib.Path) -> list[dict]:
    """Only the Orchestrator holds operational authority; the manifests must say so.

    This is the machine-readable half of docs/architecture.md. If a phase skill
    ever stops declaring 'none', a host adapter would be free to hand it tools,
    and the authority boundary would be a sentence in a document rather than a
    property of the package.
    """
    findings: list[dict] = []
    for skill_md in sorted((root / "plugins").rglob("SKILL.md")):
        fields = read_frontmatter(skill_md)
        name = fields.get("name", skill_md.parent.name)
        ref = str(skill_md.relative_to(root)).replace("\\", "/")

        if not fields.get("name") or not fields.get("description"):
            findings.append(finding("skill-discoverability", "FAIL", f"{name} is missing name or description frontmatter", ref))
        else:
            findings.append(finding("skill-discoverability", "PASS", f"{name} is discoverable by a MAF file provider", ref))

        governed = ref.split("/")[1] in GOVERNED_PLUGINS
        if not governed:
            findings.append(finding("tool-authority", "EXTERNAL", f"{name} is a capability plugin outside PMCRO governance; it may only be invoked through the Orchestrator", ref))
            continue

        # Two keys, two meanings. 'tools' says what this skill may execute.
        # 'tool_authority' points at where authority lives, which is a statement
        # of deference, not a grant - a Chief harness naming the Orchestrator is
        # declaring that it has none.
        executes = fields.get("tools")
        defers_to = fields.get("tool_authority")

        if name in AUTHORITY_SKILLS:
            if executes or defers_to:
                findings.append(finding("tool-authority", "PASS", f"{name} is the Orchestrator boundary and declares '{executes or defers_to}'", ref))
            else:
                findings.append(finding("tool-authority", "FAIL", f"{name} is an authority skill but declares no tool authority", ref))
        elif executes == "none" or defers_to:
            findings.append(finding("tool-authority", "PASS", f"{name} executes nothing ({executes or 'defers to ' + defers_to})", ref))
        elif executes:
            findings.append(finding("tool-authority", "FAIL", f"{name} claims to execute '{executes}' but is not an authority skill", ref))
        else:
            findings.append(finding("tool-authority", "FAIL", f"{name} declares no tool authority", ref))
    return findings


# Capabilities that need a running host and credentials. They are listed so the
# report states its own limits instead of letting a green preflight read as a
# working integration.
DEFERRED_TO_LIVE_HOST = [
    "instantiate MAF agents from the registry with tools and approval middleware",
    "execute an Agent Skills MCP operation (list_skills, load_skill, request_script_execution)",
    "run one end-to-end PMCRO cycle against a model endpoint",
]


def run(root: pathlib.Path, registry_path: pathlib.Path) -> dict:
    findings = check_registry(root, registry_path) + check_envelopes(root, registry_path) + check_tool_authority(root)
    failures = [f for f in findings if f["status"] == "FAIL"]
    unmapped = [f for f in findings if f["status"] == "UNMAPPED"]
    return {
        "verdict": "PASS" if not failures else "FAIL",
        "counts": {
            "pass": len([f for f in findings if f["status"] == "PASS"]),
            "fail": len(failures),
            "unmapped": len(unmapped),
            "external": len([f for f in findings if f["status"] == "EXTERNAL"]),
        },
        "deferred_to_live_host": DEFERRED_TO_LIVE_HOST,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight the MAF host adapter and MCP boundary.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--registry", default="plugins/pmcro/skills/pmcro-orchestrator/assets/agents-index.json")
    parser.add_argument("--problems-only", action="store_true", help="print only findings that are not PASS")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve() if args.root else rt.find_root(pathlib.Path(__file__))
    report = run(root, root / args.registry)
    if args.problems_only:
        report = {**report, "findings": [f for f in report["findings"] if f["status"] != "PASS"]}
    print(json.dumps(report, indent=2))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
