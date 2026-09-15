---
name: csuite-harness
description: "Coordinate Chief domain teams around high-level goals and delegate governed work to the PMCRO Orchestrator. Use for missions spanning strategy, technology, operations, product, resources, risk, security, knowledge, and learning; do not use for a single focused task."
license: MIT
compatibility: "MAF-compatible. Chiefs are tool-less; the PMCRO Orchestrator is the only operational tool authority."
metadata:
  protocol: pmcro-csuite
  framework: pmcro
  tool_authority: orchestrator-only
---

# C-suite Harness

1. Load the Chief registry and governance constraints.
2. Ask relevant Chiefs for domain proposals or DomainRequests.
3. Resolve conflicts through policy and evidence.
4. Produce an ExecutiveObjective for the PMCRO Orchestrator.
5. Let the Orchestrator discover capabilities, build PlanningContext, run O-Mode, and dispatch phases.
6. Review Orchestrator decisions and TrailFrames.
7. Approve, extend, escalate, or interrupt according to governance.

Chiefs do not call tools, phase agents, MCP, queues, webhooks, or CodeAct directly.
