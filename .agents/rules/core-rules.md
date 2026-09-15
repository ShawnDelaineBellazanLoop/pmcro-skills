---
id: core-rules
title: Core Agent Rules
alwaysApply: true
priority: high
---

# Core Agent Rules

- Use MAF Agent Skills for focused capabilities and progressive disclosure.
- Use `.agents/` for repository-wide rules and marketplace metadata; do not place `SKILL.md` files here.
- Follow the `.pmcro/` forward-only lifecycle for multi-step work.
- Never claim an artifact is complete without Checker evidence.
- Require approval for destructive actions, untrusted scripts, secrets, production changes, and governance changes.
- Prefer deterministic scripts, structured JSON envelopes, bounded retries, and append-only trails.
- Report unavailable runtimes and failed validation truthfully.
