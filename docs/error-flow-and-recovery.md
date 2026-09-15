# Error flow and recovery

PMCRO handles errors by moving forward, not by jumping backward.

```text
Checker failure → Reflector → new SeedIntent → O-Mode → bounded next cycle
```

The Reflector preserves the failure evidence and creates a concise next seed. O-Mode may select a different strategy, request research, add a constraint, require approval, escalate, or interrupt. Never retry indefinitely.

A failure is not success, and an unavailable runtime is not a passing test.
