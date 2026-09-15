---
name: clean-architecture-generic-repository
description: "Add a persisted model to a .NET clean-architecture solution using this codebase's generic repository stack - BaseEntity, IGenericRepository<T>, BaseGenericRepository<T>, JsonFileRepository<T>, and a unit of work. USE FOR: 'add an entity', 'I need to store X', 'create a repository for Y', 'scaffold a model', wiring a new type into the unit of work, or any request that would otherwise have you hand-writing CRUD. DO NOT USE FOR: scaffolding a whole new project or MCP server (that is a dotnet new template, not this), changing what a repository is allowed to do (edit the policy table), or EF Core mapping and migrations."
license: MIT
compatibility: "Requires Python 3.11+ to run the generator and a .NET 10+ SDK to build the result. Targets a solution laid out as ProjectName.Domain / ProjectName.Infrastructure. Written to be followed by a local model: every step is a command or a file, not a judgement."
metadata:
  protocol: pmcro
  tool_authority: orchestrator-only
---

# Generic repository, one model at a time

Adding a model to this codebase should cost an entity class and an attribute. Everything
else - the four verbs, the storage, the policy refusals - already exists in the base
classes. If you find yourself writing a `GetById` or a `SaveAsync`, stop: it is written.

The layering, and why each layer is there, is in
[references/layering.md](references/layering.md). Read it before changing any of the base
types; this file only covers adding a model on top of them.

## When to use

- A new thing needs to be stored: an entity plus its repository.
- A caller keeps reaching for `Repository<T>()` and wants a named property.
- Someone is about to hand-write CRUD.

## When not to use

- A whole new project or MCP server — that is a `dotnet new` template.
- Changing which verbs a resource permits — edit `.pmcro/policies/resource-operations.json`;
  that is a governance change, not a code change.
- EF Core mapping, migrations, or query tuning.

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Model name | Yes | PascalCase, singular: `Invoice`, not `Invoices` or `InvoiceEntity` |
| Resource key | Yes | The policy table key it is governed by. Must already exist in `.pmcro/policies/resource-operations.json` |
| Properties | Yes | Name and type per property. Types come from a closed list — see the schema |
| Natural key | No | The meaningful id, when there is one beyond the surrogate `Guid` |

## Workflow

### Step 1: Confirm the resource is governed

```bash
python .pmcro/scripts/resource_ops.py policy
```

If the resource key is not in that table, add it there first. A model pointing at an
unknown resource compiles and is then denied every verb at runtime — a correct failure
that is confusing to meet by surprise.

### Step 2: Write the spec

Copy [assets/example-trail-event.spec.json](assets/example-trail-event.spec.json) and edit
it. It scaffolds PMCRO's own trail event, so it shows the real shape rather than a toy.
The contract is [assets/entity-spec.schema.json](assets/entity-spec.schema.json).

Fill the spec from intent. This is the step a model does, and the reason the split exists:
turning "track invoices with a number, an amount, and a due date" into this object is a
task that can be checked. Emitting four C# files is not.

### Step 3: Validate before generating

```bash
python scripts/new_entity.py <spec.json> --check
```

Exit 0 means valid. Exit 1 lists what is wrong. Exit 3 means the resource is not in the
policy table — go back to Step 1.

### Step 4: Generate

```bash
python scripts/new_entity.py <spec.json> \
  --domain <solution>/ProjectName.Domain/Entities \
  --infrastructure <solution>/ProjectName.Infrastructure/Repositories
```

This writes `<Name>.cs` (entity plus `I<Name>Repository`) and `<Name>Repository.cs`. It
refuses to overwrite an existing file; pass `--force` only when you mean it.

### Step 5: Build

```bash
dotnet build <solution>/ProjectName.Infrastructure/ProjectName.Infrastructure.csproj
```

A clean build is the checkpoint. Do not report success without it.

### Step 6: Add a named property only if it earns one

`Repository<T>()` already works for the new model with no further wiring. Add a typed
property to `IUnitOfWork` and construct it in `UnitOfWork` only when callers keep reaching
for that type. Skipping this step is the normal outcome.

## Validation

- [ ] The resource key exists in the policy table
- [ ] `--check` exits 0
- [ ] Both files were written, neither by overwriting something
- [ ] `dotnet build` succeeds
- [ ] No CRUD was hand-written

## Common pitfalls

| Pitfall | Instead |
|---------|---------|
| Writing `GetById`, `Add`, or `SaveAsync` on the new repository | The base supplies all four verbs; the derived class stays empty |
| Omitting `[GovernedResource]` | It resolves to an unknown resource and is denied every verb — the attribute is the entire declaration |
| Inventing a property type | The schema's type list is closed on purpose; an invented type fails at build, not at validation |
| Adding a `IUnitOfWork` property for every model | Only when callers keep reaching for it |
| Expecting `SaveChangesAsync` to be transactional | The repositories are write-through today; it returns 0 and the docs say why |

## References

- [references/layering.md](references/layering.md) — the stack, and why each layer exists
