# Earned constraint promotion

A failure may produce an earned-constraint candidate, but it does not automatically rewrite constitutional laws.

```text
failure → CheckReport → ReflectionFrame → candidate → review → active constraint → regression enforcement
```

## Promotion requirements

- Link the source CheckReport and TrailFrame.
- State the exact failure pattern and scope.
- Define enforcement points.
- Assign confidence and an owner.
- Add or identify a regression test.
- Require governance review for security, legal, destructive, production, or constitutional changes.

Active constraints are loaded during Planner preflight, included in Maker contracts, checked by Orchestrator policy, and tested by Checker regressions. Constraints may be suspended, retired, or superseded with a new evidence-backed frame.
