# PMCR-O .NET Patterns

House .NET patterns for this codebase. It complements the Microsoft `dotnet` plugins
rather than competing with them: those carry general .NET and C# guidance, this carries
the conventions this codebase has settled on. Install both.

## Skills

- **clean-architecture-generic-repository** — the entity and repository stack:
  `BaseEntity` with a generated `Guid` identity, `IGenericRepository<T>` with overloaded
  `Get`, a `BaseGenericRepository<T>` that implements every verb once, and per-model
  repositories that are empty because there is nothing left for them to do. Includes a
  spec schema and a generator, so adding a model does not mean writing CRUD again.

- **mcp-server-project** *(not yet built)* — the three-pillar MCP server layout:
  configuration, tools, resources, prompts.

## Why a generator rather than instructions

A frontier model will improvise four correct files from a paragraph of prose, which makes
a generator look unnecessary. A small local model will produce something that looks like
C# and does not compile, and will not say so.

So the work is split where it can be checked: the model turns intent into an
`EntityScaffoldSpec` — small, structured, and rejected when it is wrong — and
`scripts/new_entity.py` turns that spec into files deterministically. Neither half asks a
model to be right about code it cannot verify.

For a whole project rather than a file, the same logic points at a real `dotnet new`
template carried in `assets/`, driven by a script. `dotnet/skills` already ships a
`dotnet-template-engine` plugin covering discovery, scaffolding, and template authoring —
depend on it rather than reimplementing templating here.

## Governance

Generated repositories are governed by `.pmcro/policies/resource-operations.json`. A model
declares which resource it is with `[GovernedResource("...")]`, and the base repository
refuses the verbs that resource refuses. A model that forgets the attribute resolves to a
resource the policy does not know, and unknown resources are denied — forgetting fails
closed rather than open.
