# Runbooks

Order inside each runbook: Symptom → This may be working as designed → Diagnose → Fix → Escalate.

| Runbook | Symptom |
|---|---|
| [llm-provider-outage.md](llm-provider-outage.md) | Chat returns `upstream_unavailable` or hangs |
| [db-down.md](db-down.md) | `/readyz` reports `db: fail`; tools return `internal_error` |
| [tool-loop-runaway.md](tool-loop-runaway.md) | Answers end with `max_iterations`; many audit rows per trace |
| [rate-limit-storm.md](rate-limit-storm.md) | Many `429`s or `rate_limited` envelopes |
| [mcp-unreachable.md](mcp-unreachable.md) | API `readyz.checks.mcp` fails; every step `upstream_unavailable` |
