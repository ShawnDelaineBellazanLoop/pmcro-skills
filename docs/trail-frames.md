# Trail Frames

A TrailFrame is durable verified state. A TrailEvent records that something happened. The Trail indexes both.

Common frame types:

```text
IntentFrame GoalFrame ResearchFrame PlanFrame
ToolRequestFrame ToolResultFrame ArtifactFrame
CheckFrame ReflectionFrame DecisionFrame HandoffFrame
```

Frames should contain evidence references, provenance, confidence, hashes, schema version, cycle ID, phase, and timestamps. Do not store private chain-of-thought. Store concise decision summaries and observable evidence instead.
