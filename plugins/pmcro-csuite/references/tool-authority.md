# Single tool authority

The PMCR-O C-suite uses a single tool-authority model:

```text
C-suite Chiefs       -> no direct tools
PMCRO phase agents   -> no direct tools
PMCRO Orchestrator   -> only operational tool caller
Human/policy gate    -> approval authority for high-risk actions
```

Phase agents may emit a typed `ToolIntent`, but they never execute it. The Orchestrator validates the request against laws, constraints, resource policy, path policy, and approval requirements; executes the tool; records stdout, stderr, exit code, hashes, and evidence references; then returns a typed `ToolResult`.

## ToolIntent contract

```json
{
  "type": "ToolIntent",
  "phase": "maker",
  "tool": "run_skill_script",
  "purpose": "Create the requested artifact",
  "arguments": {},
  "risk": "write",
  "requires_approval": true
}
```

## Authority levels

- Read-only local inspection: Orchestrator may execute when the skill source is trusted.
- Normal writes: policy check and approval according to the active configuration.
- Destructive, production, secret, security, or governance actions: human or external policy approval is required.

CodeAct is an execution capability behind this boundary, not a replacement for PMCRO governance. Slash commands are host UI syntax, not the inter-agent protocol.
