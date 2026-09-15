# The layering, and why each layer is there

Read this before changing any base type. Adding a model on top of them needs only
`SKILL.md`.

## The stack

```text
BaseEntity                         Guid Id = Guid.NewGuid(), CreatedUtc
  IGenericRepository<T>            Get() / Get(id) / Get(predicate) / Add / Update / Delete
    BaseGenericRepository<T>       every verb, once, with the policy guard
      IJsonFileRepository<T>       adds FilePath
      JsonFileRepository<T>        atomic file storage
        TrailFrameRepository       empty
```

Interfaces mirror the classes: a per-model interface inherits `IGenericRepository<T>` and
lives in Domain, while `IJsonFileRepository<T>` lives in Infrastructure. That split is
deliberate — the domain says *what it needs*, never *how it is stored*. A per-model
interface that inherited the JSON one would drag storage into Domain and invert the
dependency.

## Why identity is generated in the constructor

`Id` is assigned at construction, not by the store, so a new entity is addressable before
it is saved. Something else in the same unit of work can reference it, and a write that
fails halfway leaves records that still point at each other correctly.

The surrogate `Guid` does not replace a meaningful key. Control-plane records carry their
own — `FrameId`, `ConstraintId`, `EventId` — and those are looked up through the predicate
overload of `Get`. Making one field do both jobs is how ids end up meaning two things.

## Why the guard is in the base

`BaseGenericRepository<T>` consults the policy table before touching the store. It sits
there rather than in each repository because a gate every derived class must remember to
call is a gate one of them will forget, and the one that forgets is the one that matters.

The resource comes from `[GovernedResource("...")]` on the model, so a model nobody wrote
special-case code for is still governed. A model with no attribute resolves to a name the
table does not know, and unknown resources are denied — forgetting fails closed.

Three decisions, not two:

| Decision | Meaning | Behaviour |
|----------|---------|-----------|
| `allow` | Proceed | Runs |
| `approval` | Legitimate, needs a person | `ApprovalRequiredException` unless `IApprovalContext` says a human authorized it |
| `deny` | Never valid here | `PolicyDeniedException`, with the rule quoted |

They throw rather than return false. A denied write a caller can ignore is a write that
eventually happens.

`IApprovalContext` is an abstraction rather than a boolean argument because approval is a
fact about the session — who said yes, to what, when — and the implementation is where
that gets recorded. There is deliberately no default implementation returning true; that
would make the gate decorative.

## Why storage is abstract

`BaseGenericRepository<T>` leaves `LoadAsync` and `PersistAsync` abstract. Whether records
live in JSON, a database, or memory is not a governance concern, and keeping it out means
the policy behaviour is testable with no store at all.

`JsonFileRepository<T>` writes to a temp file and renames it into place. The control plane
is files a person can read in a diff, which is most of why it is trustworthy — and a
machine that stops mid-write must leave the previous version intact rather than a
truncated one. That failure is the environment this runs in, not a hypothetical.

## What the unit of work does and does not do

It builds repositories once and caches them, so two callers get the same instance and
cannot stage changes past each other. Named properties are ergonomics; `Repository<T>()`
is the part that matters, because it means a new model needs no property, no registration,
and no interface.

`SaveChangesAsync` returns 0 today, and says so. The repositories are write-through, so
there is nothing staged to commit — the atomicity a unit of work implies is **not** in
force. It becomes real when the repositories stage their writes or an EF Core `DbContext`
sits behind them and owns the transaction. Until then the method is a seam, and saying
that is better than shipping something that looks transactional.

## Where this stops

No EF Core, no migrations, no query translation — `Get(predicate)` filters in memory after
loading, which is fine for control-plane collections and wrong for a real table. When a
model outgrows that, it needs a repository backed by a `DbContext`, not a bigger
`JsonFileRepository`.

## Resources

- `.pmcro/policies/resource-operations.json` — the table every repository answers to
- `ProjectName.Domain/Common/` — `BaseEntity`, `IGenericRepository<T>`, `IUnitOfWork`
- `ProjectName.Infrastructure/Repositories/` — the base, the JSON storage, the empty ones
