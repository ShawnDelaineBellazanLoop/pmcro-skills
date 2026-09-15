# PMCRO checkpoints

| Stage | Required checkpoint |
|---|---|
| Planner | Confirm source root, output path, exclusions, and overwrite policy. |
| Maker | Run one explicit script with absolute paths. |
| Checker | Verify files, counts, hashes, and archive members. |
| Reflector | Record errors, deviations, and corrections. |
| Orchestrator | Chain only successful stages; stop on first failure. |

A manual fallback must provide the exact command and the expected postcondition. Never silently substitute an unverified operation.