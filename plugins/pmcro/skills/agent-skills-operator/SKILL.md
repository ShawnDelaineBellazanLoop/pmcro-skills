---
name: agent-skills-operator
description: "Discover and describe plugins, Agent Skills, skill resources, scripts, MCP servers and tools, host tools, CodeAct profiles, queues, webhooks, and filesystem/process adapters for the PMCRO Orchestrator. Use for capability inventory and policy-aware selection; do not execute tools directly from this skill."
license: MIT
compatibility: "MAF-compatible. Discovery sources are supplied by the Orchestrator host adapter, MAF provider, plugin registry, and optional Agent Skills MCP server."
metadata:
  protocol: pmcro
  tool_authority: orchestrator-only
---

# Agent Skills Operator

Provide the Orchestrator with one normalized CapabilityCatalog.

## Discovery sources

- **Marketplace:** marketplaces, plugins, manifests, versions.
- **MAF provider:** skills, `SKILL.md`, skill resources, and skill scripts.
- **MCP registry:** MCP servers and MCP tools.
- **Host adapter:** Claude/MAF host tools, filesystem, process, desktop, and approval capabilities.
- **PMCRO runtime:** CodeAct profiles, queues, webhooks, checkpoints, Trail, and policy adapters.

## Operations

1. List all configured capability sources.
2. Normalize results into `CapabilityCatalog` records.
3. Describe inputs, outputs, risk, provider, resources, scripts, and allowed callers.
4. Move records through `discovered → described → trusted → selected → approved → executed → verified`.
5. Return only selected capability descriptions to phase agents.
6. Convert execution requests into ToolIntent objects for the Orchestrator.
7. Record discovery, selection, approval, ToolResult, and verification as TrailFrames.

## Boundaries

Discovery is not permission. Trust is not approval. Execution is not verification. Phase agents and Chiefs do not call capability sources directly. Only the PMCRO Orchestrator may invoke tools or adapters.
