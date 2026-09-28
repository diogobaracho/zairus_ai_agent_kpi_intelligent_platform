# Connect Claude Desktop and Cursor to the MCP server

The server exposes four read-only tools: `search_companies`, `list_company_kpis`,
`get_kpi_history`, `get_kpi_qtd` ([reference](../reference/mcp-tools.md)).

## Option A: stdio (desktop clients spawn the server)

Requires Postgres running (`make up` or `docker compose up -d postgres` + `make migrate seed`).

1. Find the absolute path of the repository, e.g. `/home/me/kpi-platform`.
2. Add to Claude Desktop's `claude_desktop_config.json` (macOS:
   `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`) or Cursor's
   `.cursor/mcp.json` (project) / `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "kpi-platform": {
      "command": "uv",
      "args": ["run", "--project", "services/mcp", "python", "-m", "kpi_mcp", "--transport", "stdio"],
      "cwd": "/home/me/kpi-platform",
      "env": {
        "KPI_DATABASE_URL": "postgresql+asyncpg://kpi:kpi@localhost:5432/kpi",
        "KPI_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

3. Restart the client. The tools appear under the `kpi-platform` entry (the server itself reports
   the `mcpServerName` from `brand.config.json`).
4. Ask: *Which KPIs does ORBY publish, and what is its latest QTD total revenue?*

Ready-made files: `infra/mcp-clients/claude_desktop_config.example.json`,
`infra/mcp-clients/cursor.mcp.example.json`.

## Option B: HTTP (server already running from `make up`)

Cursor and other clients that support streamable HTTP:

```json
{ "mcpServers": { "kpi-platform": { "url": "http://localhost:8090/mcp" } } }
```

For Claude Desktop, use the "Add custom connector" dialog with the same URL (requires a version
that supports remote MCP over HTTP; otherwise use stdio).

## Example tool calls (what the client sends and receives)

```json
// request
{"name":"get_kpi_qtd","arguments":{"ticker":"ORBY","kpi":"total_revenue"}}
// result (structuredContent)
{"company":{"ticker":"ORBY","name":"Orbitly Analytics","sector":"Software"},
 "kpi":{"slug":"total_revenue","name":"Total Revenue ($MM)","unit":"$MM"},
 "period":"2026Q3","latest":{"as_of":"2026-09-15","value":231.4,"unit":"$MM"},
 "snapshots":[...],"prior_quarter":{"period":"2026Q2","value":228.9},"note":null,"trace_id":"..."}
```

```json
// request with a typo
{"name":"get_kpi_history","arguments":{"ticker":"ORBY","kpi":"Totl Revenue"}}
// isError: true, text content:
{"error":{"code":"kpi_not_found","message":"KPI 'Totl Revenue' not found for ORBY",
 "suggestions":[{"value":"total_revenue","label":"Total Revenue ($MM)","score":95.2}],
 "recovery_hint":"Retry with kpi set to suggestions[0].value, or call list_company_kpis.",
 "retryable":true,"trace_id":"..."}}
```

## Verify

```bash
uv run python scripts/mcp_smoke.py --stdio      # lists 4 tools, calls get_kpi_qtd ORBY total_revenue
uv run python scripts/mcp_smoke.py --url http://localhost:8090/mcp
python3 -m json.tool infra/mcp-clients/claude_desktop_config.example.json > /dev/null && echo valid
```

Every call from the desktop client shows up in `GET http://localhost:8080/v1/audit/tool-calls`.

## What usually goes wrong

- **Server shows as failed in the client**: logs go to stderr; run the `command` manually in a
  terminal and read the error. Usually `KPI_DATABASE_URL` or `uv` not on the client's PATH
  (use the absolute path to `uv`).
- **Nothing on stdout but JSON is expected**: stdio mode must never print to stdout; the
  logging config sends everything to stderr.
- **Tools listed but calls fail with `rate_limited`**: the desktop client retried aggressively;
  raise `KPI_MCP_RATE_LIMIT_BURST`.
