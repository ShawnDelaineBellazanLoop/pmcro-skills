# Security Policy

## Supported Versions

This repo publishes a single rolling `catalog/skills.json` index versioned independently
of any consuming project (e.g. `ProjectName`). Only the latest commit on `main` is supported.

## Reporting a Vulnerability

If a skill package in this catalog contains a script, prompt, or dependency reference that
could lead to unsafe or unintended command execution (e.g. an `AutoMutating`/`RequiresHil`
boundary violation per Colony Law), please report it privately rather than opening a public
issue:

1. Open a [private security advisory](../../security/advisories/new) on this repository, or
2. Email the maintainer directly (see repository owner contact).

Do not include working exploit payloads in a public issue. Include:

- the affected skill path (e.g. `catalog/Tools/Git/skills/git/`)
- the specific script or command in question
- expected vs. actual behavior

## Scope Notes

Skills in this catalog are declarative capability packages (`SKILL.md`, `manifest.json`,
`scripts/`, `references/`). They are consumed by the PMCRO Colony's Terminal MCP, which
enforces its own `TerminalCommandPolicy` tiering (`AutoReadOnly` / `AutoMutating` /
`RequiresHil`, default-deny). A vulnerability in a skill script is a vulnerability in the
*content the policy engine evaluates*, not a bypass of the policy engine itself — please
flag both distinctly if you find one.
