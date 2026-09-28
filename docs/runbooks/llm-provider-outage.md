# LLM provider outage

**Symptom**: chat streams `session` then `error {code: upstream_unavailable}`; logs show
`llm_turn` with `error: RateLimitError|APIConnectionError|APIStatusError 5xx`.

**Working as designed?** The SDK retries twice with backoff; a `429` from the vendor after that
is surfaced instead of queued. Partial steps are persisted with `stopped_reason: provider_error`.

**Diagnose**: `docker compose logs api | grep llm_turn | tail`; check `ANTHROPIC_API_KEY`
validity (`AuthenticationError` → 401 mapped to `upstream_unavailable` with `reason: auth`);
check vendor status page.

**Fix**: switch to the stub for a demo (`KPI_LLM_PROVIDER=stub`, restart API), rotate the key, or
lower load. The REST API and MCP server are unaffected.

**Escalate**: if `readyz.checks.llm_provider` is `configured` but every call fails for > 15 min.
