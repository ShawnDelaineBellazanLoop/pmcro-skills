# Chief Router Template (Package-Scoped, Catalog-Driven)

## What this is — and what it is not
This is the generic, reusable shape for a package-scoped router (e.g. `cto` in
Agent-Foundry, or a future `cfo`/`cmo`/etc. in another package). It is **not** a
PMCR-O cycle instance and has no relationship to `pmcro-base` or any cycle-template
schema. A router does not Plan, Make, Check, or Reflect — it reads a request and hands
off to exactly one skill in its own package. Never give it Plan/Make/Check/Reflect
sections; that would misrepresent what it does.

## The routing table is catalog-driven, not hand-typed
Earlier drafts of this pattern hand-authored the routing table as static rows. That's
wrong for two reasons: (1) it drifts out of sync with the catalog the moment a skill is
added, renamed, or removed, and (2) a hand-typed row for a package with nothing real in
it is a placeholder (PLAN-001), no matter how declaratively it's framed.

The fix: **a chief's routing table is built at read-time by filtering
`catalog/skills.json` on `path`.** A chief owns every entry whose `path` starts with its
own package's `skills/` prefix — the same prefix its own `agents/<role>/AGENT.md` is a
sibling to. Nothing is asserted that isn't already true in the catalog.

```
catalog/<Lane>/<Package>/agents/<role>/AGENT.md   ← the router
catalog/<Lane>/<Package>/skills/*/                ← everything it routes to
```

For `cto`, the prefix is `catalog/Tools/Agent-Foundry/skills/`. For a hypothetical
future `cfo` under a Finance package, the prefix would be `catalog/Finance/<Package>/skills/`.

**Do not use `category` for this filter.** `category` in `skills.schema.json` is
free-text but already means *functional* category (`Meta`, `VersionControl`, etc.), not
*which chief owns this skill*. Reusing it for chief-ownership would silently overload a
field that already has a meaning, and would require re-tagging every existing skill.
Path-prefix filtering needs zero schema changes and zero re-tagging — it's already true
by construction.

## What "catalog-driven" means at read-time
The router (an LLM reading `AGENT.md`, not compiled code) does this at the start of
every session or whenever routing is ambiguous:
1. Read `catalog/skills.json`.
2. Filter entries where `path` starts with this router's own package prefix.
3. Build the routing table from each matching entry's `name` and `description`
   (the `USE FOR` / `DO NOT USE FOR` lines are the signal-phrase source — don't invent
   new phrasing).
4. If the filtered set is empty, say so plainly: *"No skills are registered under
   [package] yet."* An empty result is an honest statement about the catalog's current
   state, not a failure of the router.

This is why scaffolding a full C-suite is legitimate under this design: an
uninstantiated chief with an empty filtered set isn't a lie or a placeholder — it's a
router truthfully reporting nothing exists yet. The moment a real skill is added under
its package with a matching path, that chief starts routing to it with zero edits to
the chief's own file.

## Required frontmatter
```yaml
---
name: <lowercase-package-role, e.g. cto>
description: "Package-scoped router for <Package>. Use when the requester's need is
  about <package's domain> but it isn't obvious which specific skill handles it. If
  the requester already names the exact skill they want, skip this router. Routing
  table is built from catalog/skills.json filtered on this package's path prefix —
  not hand-typed."
skills: []   # deliberately empty — populated dynamically at read-time, never hand-listed here
---
```

## Required sections
- **Role** — one sentence: routes ambiguous requests to the right skill in this
  package; does not do the work itself.
- **Owns** — reading the request, filtering the catalog by this package's path prefix
  to build the current routing table, asking at most one clarifying question when
  genuinely ambiguous, sequencing multi-skill requests explicitly.
- **Does Not Own** — the actual work (that belongs to the named skill), routing outside
  the package, hand-maintaining a static table.
- **Routing Procedure** — the four-step catalog-filter procedure above, restated for
  this specific package's path prefix.
- **Invariant Enforcement** — must include: (a) never invents a skill for something
  that's a variant of an existing one; (b) never does the work itself; (c) never
  hardcodes a routing row — if the catalog changes, the table changes, with no edit to
  this file.

## Where a router lives
`catalog/<Lane>/<Package>/agents/<role>/AGENT.md` — sibling to that package's `skills/`
folder, never inside it. Routers stay invisible to the Directory/marketplace card on
purpose (they don't appear in `plugin.json`'s `skills` array) — they're internal triage
logic, not a capability a user installs.

## Instances of this template

| Package | Router | Path prefix filtered | Notes |
|---|---|---|---|
| Agent-Foundry | `cto` | `catalog/Tools/Agent-Foundry/skills/` | First instance. Currently resolves to skill-creator, git, plugin-packager, pmcro-loop (catalog-check pending registration). |

Add a row here only when a real package with 2+ skills actually exists under it — not
in anticipation of one. An empty-filter chief (e.g. a future `cfo` with zero Finance
skills registered) is fine to scaffold *once a Finance package folder genuinely exists*
to filter against — scaffolding one with no package folder at all is still PLAN-001.
