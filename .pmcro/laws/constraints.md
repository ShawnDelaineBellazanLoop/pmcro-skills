# Runtime constraints

```yaml
max_cycles: 5
max_phase_attempts: 2
max_wall_time_seconds: 1800
max_output_bytes: 10485760
max_trail_event_bytes: 1048576
require_human_approval_for:
  - destructive_filesystem_operation
  - production_deployment
  - secret_access
  - governance_change
  - untrusted_script
allowed_verdicts:
  - ACCEPT
  - EXTEND
  - LOOP
  - ESCALATE
  - INTERRUPT
```

When a constraint is reached, stop the current operation and emit a structured decision. Never bypass a limit by silently starting an untracked cycle.
