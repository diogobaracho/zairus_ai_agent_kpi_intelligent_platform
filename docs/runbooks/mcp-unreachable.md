# MCP unreachable from the API

**Symptom**: `/readyz` → `checks.mcp: fail`; chat steps all `status: error, code:
upstream_unavailable`; `/v1/meta/tools` → 503.

**Working as designed?** The API refuses to answer from memory; the boundary is intentional.

**Diagnose**: `curl localhost:8090/healthz`; `KPI_MCP_URL` (must end with `/mcp`); network
policy between the two services; MCP logs.

**Fix**: restart MCP; correct the URL; for single-container deployments switch to
`KPI_MCP_MODE=inprocess`.

**Escalate**: if MCP is healthy but the API still fails (transport/protocol version mismatch;
check pinned `fastmcp` versions on both sides).
