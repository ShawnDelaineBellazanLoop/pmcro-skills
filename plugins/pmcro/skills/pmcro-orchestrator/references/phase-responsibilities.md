# PMCRO phase responsibilities

## Orchestrator

Load the active `.pmcro` configuration, laws, constraints, Trail manifest, current frames, earned constraints, high-level goal, and validated resource manifest. Resolve the current phase, select a bounded strategy, dispatch a typed message, enforce approvals and limits, and record the transition. Do not perform phase work.

## Planner

Turn a messy seed into a structured IntentEnvelope: surface intent, truest intent, unstated constraints, confidence, assumptions, validated resource references, and out-of-scope ideas. Produce the smallest PlanEnvelope with observable acceptance criteria. Do not invent missing facts or create artifacts.

## Maker

Execute only the approved plan using validated resources and deterministic scripts. Create complete artifacts, record paths and hashes, and escalate impossible work. Do not silently skip, stub, overwrite, or declare acceptance.

## Checker

Independently inspect the artifact and ground truth. Run validators, tests, schema checks, and postcondition checks. Score the acceptance criteria and emit an evidence-backed verdict. Do not repair the artifact or rely on Maker claims.

## Reflector

Summarize what evidence proves, identify reusable patterns, emit learning frames, add durable earned constraints, and create the next-cycle seed. Do not hide uncertainty or store private chain-of-thought.

## Forward-only lifecycle

```text
Planner → Maker → Checker → Reflector → Orchestrator
```

A failure flows forward to Reflector. Orchestrator may open a new bounded cycle; no phase directly invokes an earlier phase.
