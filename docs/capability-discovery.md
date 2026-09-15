# Capability discovery

The Agent Skills Operator builds one normalized CapabilityCatalog from several sources:

```text
marketplace → plugins → skills → resources/scripts
MCP registry → MCP servers/tools
host adapter → Claude/MAF/filesystem/process/desktop tools
PMCRO runtime → CodeAct/queues/webhooks/checkpoints/Trail adapters
```

MAF automatically discovers configured skill packages, not arbitrary MCP or host tools. The Orchestrator explicitly loads each source and normalizes records.

## State pipeline

```text
discovered → described → trusted → selected → approved → executed → verified
```

Never collapse these states. A discovered capability can be blocked by policy; an executed result still requires Checker verification.

The catalog is an inventory, not an execution permission list. Only the Orchestrator has operational authority.
