---
id: pmcro-lifecycle
title: PMCRO Lifecycle
triggers:
  - multi-step workflow
  - create or modify agent skill
  - validate generated artifact
scope:
  - .pmcro/**
  - plugins/**
  - tests/**
---

Use Planner -> Maker -> Checker -> Reflector -> Orchestrator. Failures flow forward to Reflector; the Orchestrator decides whether to loop, extend, escalate, interrupt, or accept. Store evidence and decisions, not hidden chain-of-thought.
