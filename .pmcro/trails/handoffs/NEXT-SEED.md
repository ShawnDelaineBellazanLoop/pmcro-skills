# Next seed

Paste this to start the next session.

---

Activate PMCRO on `W:\projects\pmcro-skills` and resume from
`.pmcro/trails/handoffs/RESUME.json`. Read it first — it carries the AppHost port, the
workspace sandbox design, the scaffolding split, and the open gates. Verify the starting
state with `python .pmcro/tests/run_all.py` before changing anything.

Work the next steps in RESUME order, embodying the framework as you go: claim before you
start, heartbeat as you write, Checker evidence before any ACCEPT, and record frames
rather than editing them.

First: finish the `pmcro-dotnet` plugin so it is actually installable —
`.codex-plugin/plugin.json`, `version.json`, `README.md`, the `SKILL.md` and
`references/` for `clean-architecture-generic-repository` (the assets and script already
exist and are proven), add `pmcro-dotnet` to `GOVERNED_PLUGINS` in
`validate_host_boundary.py`, and register it across all five marketplace manifests.

Then: the `mcp-server-project` skill, carrying the archive's three-pillar layout
(`W:\projects\pmcro-runtimearchive\mcp\`) as a real `dotnet new` template in `assets/`,
driven by a script rather than a hand-rolled renderer. Include the
`ExcludeAssets="analyzers"` detail — it is the kind of thing that costs an afternoon.

Standing constraints: extend `dotnet/skills`, never fork it. Research version-sensitive
facts against nuget.org and Microsoft Learn rather than recalling them. A live MAF host
still needs a model endpoint and credentials, which is `secret_access` under LAW-008 and
waits for me.

---

## Using the plugins in that session

```
/plugin marketplace add W:\projects\pmcro-skills
/plugin install pmcro@pmcro-skills-marketplace
```

Installing `pmcro` brings its skills, the `laws-operator` agent, and `hooks/hooks.json`,
which is auto-discovered — no `plugin.json` entry needed for it to load.

`pmcro-dotnet` will not appear until it is registered in the manifests; that is the first
task above.

Note: in a repository with no `.pmcro/` directory, the control-plane guard finds no policy
and exits 0. That is intended — it governs control planes, not every repository you open.
