# Add an MCP tool

Worked example: `compare_kpi_across_companies(tickers, kpi, period)`. Target time: 20 minutes
including tests.

1. **Model** (`packages/kpi_core/src/kpi_core/models.py`): add `KpiComparison(kpi, period,
   rows: list[ComparisonRow])` with `ComparisonRow(company, value, unit, rank)`.
2. **Service** (`packages/kpi_core/src/kpi_core/services/estimates.py`): add
   `async def compare_kpi(ctx, repo, *, tickers: list[str], kpi: str, period: str) ->
   KpiComparison`. Resolve each ticker with `companies.resolve_company` (raises
   `CompanyNotFound` with suggestions), resolve the KPI once with `kpis.resolve_kpi`, validate the
   period, fetch one point per company, sort by value. Cap `tickers` at 10.
3. **Unit tests** (`packages/kpi_core/tests/test_services_estimates.py`): happy path, unknown
   ticker among many (partial failure → error listing which one, with suggestions), KPI typo,
   period with no data for one company (row with `value: null` + note).
4. **Tool** (`services/mcp/src/kpi_mcp/tools.py`): add a function decorated with
   `@mcp.tool(annotations=READ_ONLY, tags={"kpi"})`, typed parameters (`tickers: list[TickerArg]`,
   `kpi: KpiArg`, `period: PeriodArg`), a one-paragraph docstring saying *when* to use it, and a
   body that calls the service through `run_tool(...)` (which maps `KpiError` to the envelope).
5. **Register** it in `create_server` (same file or `server.py` if tools are split per module).
6. **Snapshot**: run `uv run pytest services/mcp -k snapshot --snapshot-update` and review the
   diff of `docs/reference/mcp-tools.json`; update the table in
   `docs/reference/mcp-tools.md` (or run `make tool-docs`).
7. **MCP tests** (`services/mcp/tests/test_tools_compare.py`): call through
   `fastmcp.Client(server)`; assert `structured_content`, the envelope for a bad ticker, and that
   an audit row was written.
8. **Agent prompt** (`services/api/src/kpi_api/agent/prompts.py`): if the tool should be preferred
   for "compare" questions, add one sentence. The agent picks up the schema automatically.
9. **Docs**: the reference table in `docs/reference/mcp-tools.md` and `make tool-docs`.

## Verify

```bash
uv run pytest services/mcp packages/kpi_core -q
make mcp-http & uv run python scripts/mcp_smoke.py --url http://localhost:8090/mcp --tool compare_kpi_across_companies \
  --args '{"tickers":["ORBY","KSTL"],"kpi":"total_revenue","period":"2026Q2"}'
```

Expected: two rows ranked by value, plus a `tool_call_audit` row with `tool_name =
compare_kpi_across_companies`.

## What usually goes wrong

- Forgetting `additionalProperties: false` compatibility: keep parameters to scalars and lists
  of scalars so the agent can mark the schema `strict`.
- Raising a plain `ValueError`: it becomes a masked `internal_error`; raise a `KpiError`.
- Returning a dict instead of a Pydantic model: still works, but you lose the output schema that
  the client shows to the model.
