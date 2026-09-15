# Seed to true intent

Treat a user seed as mixed material, not a complete specification. Separate literal request, desired outcome, requirements, wishes, speculative ideas, blocked dependencies, and out-of-scope material.

Produce a confidence-rated hypothesis:

```json
{
  "surface_intent": "literal request",
  "truest_intent": "outcome that would make the request successful",
  "required": [],
  "desired": [],
  "speculative": [],
  "blocked": [],
  "out_of_scope": [],
  "unstated_constraints": [],
  "confidence": "high|medium|low",
  "clarification_needed": []
}
```

Read the active goal, Trail, earned constraints, laws, and validated resource manifest before planning. If uncertainty changes safety or scope, request clarification or escalate. Do not claim to know hidden intent with certainty.
