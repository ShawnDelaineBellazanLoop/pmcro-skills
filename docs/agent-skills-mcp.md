# Agent Skills MCP

Use an Agent Skills MCP server when skill discovery or execution must be shared across processes, machines, or hosts.

Recommended operations:

```text
list_plugins
list_skills
describe_skill
load_skill
read_skill_resource
inspect_skill_script
request_script_execution
```

MCP is a capability transport, not the PMCRO state model. The Orchestrator calls the MCP server, applies policy, records ToolResult and TrailFrame data, and returns structured results to agents.

Do not give every phase agent direct MCP access. Keep the MCP client or adapter on the Orchestrator side unless a specific read-only capability is deliberately exposed.
