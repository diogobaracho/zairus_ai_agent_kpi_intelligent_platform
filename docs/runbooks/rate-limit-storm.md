# Rate-limit storm

**Symptom**: many `429` from the API or `rate_limited` envelopes from MCP.

**Working as designed?** Per-IP token bucket protects the service; behind a shared NAT many
users look like one IP.

**Diagnose**: `http_request` log lines with `status: 429` grouped by `client_ip`; check whether
a single client is misbehaving or the limits are too low for the deployment.

**Fix**: raise `KPI_RATE_LIMIT_*` / `KPI_MCP_RATE_LIMIT_*`; put limits at the edge; plan the
Redis limiter (future improvements).

**Escalate**: sustained abuse from one source (block at the proxy).
