# MAF Agent Skills — How the Runtime Actually Works

Verified against Microsoft's own Agent Skills documentation and the `agent-framework`
design decision record (0021-agent-skills-design), not assumed. This is the ground truth
`skill-creator` authors against.

## The Three Building Blocks

1. **Provider** — `AgentSkillsProvider` (C#) or `SkillsProvider` (Python). A context
   provider that exposes skills to an agent: advertises available skills in the system
   prompt and registers the tools the agent uses to load skills, read resources, and run
   scripts.
2. **Sources** — supply skills to the provider. Three source types:
   - **File-based** — discovered from `SKILL.md` files in filesystem directories.
     Resources and scripts are files in subdirectories. **This is what `pmcro-skills`
     produces.**
   - **Programmatic** — defined in C# code, either:
     - *Inline* — built at runtime via `AgentInlineSkill`. Good for quick,
       agent-specific, throwaway skill definitions.
     - *Class-based* — reusable C# classes subclassing `AgentClassSkill`. Good for
       packaging skills as shared libraries or NuGet packages.
   - **Class-based skills** (Python: `Skill`) — similar concept, code-defined.
3. **Builder** — `AgentSkillsProviderBuilder` composes multiple sources (file-based +
   class-based + inline) into one provider with automatic aggregation, deduplication,
   and caching. Use this when `ProjectName`'s UI needs to load both `.agents/skills/`
   (this catalog) and any inline/class-based skills defined directly in C#.

## The Three Tools an Agent Actually Calls

- `load_skill` — load a skill's instructions (the `SKILL.md` body). **Always advertised.**
- `read_skill_resource` — fetch a bundled resource (something in `references/` or
  `assets/`). Advertised **only if at least one skill has resources.**
- `run_skill_script` — execute a bundled script (something in `scripts/`). Advertised
  **only if at least one skill has scripts.**

This is why `skill-creator`'s Bootstrap step says not to create empty `scripts/` or
`references/` folders "just in case" — an empty folder still counts as present and will
cause MAF to advertise a tool with nothing behind it.

## Four-Stage Progressive Disclosure

`advertise skill names → load instructions → read resources → run scripts`

This is the actual mechanism behind what `dotnet-agent-skills` and Anthropic's own
`skill-creator` both call "progressive disclosure." It's not a convention either project
invented — it's how MAF's context window management works natively. Keep `SKILL.md`
lean for the same reason Anthropic's skill-creator recommends staying under ~500 lines:
the body loads into context on every trigger, resources only load on demand.

## Governance: Script Execution Requires Approval

Per Microsoft's own guidance: *"Agent Skills should be treated like any third-party code
you bring into your project"* — review content and scripts before use, verify a script's
actual behavior matches its stated intent. MAF supports a human-approval mechanism for
`run_skill_script` calls specifically.

This maps directly onto the Colony's existing `TerminalCommandPolicy` tiers:

| MAF concept | Colony equivalent |
|---|---|
| `run_skill_script` requiring approval | `AutoMutating` / `RequiresHil` tiers |
| `load_skill` / `read_skill_resource` (read-only) | `AutoReadOnly` tier |
| Sandboxing (limit filesystem/network/system access to only what's required) | Terminal MCP's default-deny posture |
| Audit and logging of loaded skills/resources/scripts | Trail sealing under `.pmcro/trails/` |

Two governance systems already agree here — the recommendation from the earlier
architecture-proposal session (wire Colony Law into MAF's actual approval predicate
instead of running two parallel systems) holds up against the verified spec.

## Skills vs. Workflows

MAF draws this distinction explicitly: with a **skill**, the AI decides how to execute the
instructions (adaptive). With a **workflow**, you explicitly define the execution path
(deterministic). A Colony **trail** is closer to a workflow than a skill — it's a defined
business process that *consumes* skills, not a skill itself. Keep that distinction in mind
when someone asks "should this be a skill or a trail."

## Source

- https://learn.microsoft.com/en-us/agent-framework/agents/skills
- https://github.com/microsoft/agent-framework/blob/main/docs/decisions/0021-agent-skills-design.md
- https://devblogs.microsoft.com/agent-framework/agent-skills-for-net-is-now-released/
