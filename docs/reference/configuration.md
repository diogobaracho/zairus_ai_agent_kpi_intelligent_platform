# Configuration

pydantic-settings, prefix `KPI_`, `.env` file supported, every default works locally.

| Variable | Default | Used by | Meaning |
|---|---|---|---|
| `KPI_ENV` | `local` | all | `local\|test\|staging\|production`; production enables strict validators |
| `KPI_LOG_LEVEL` | `INFO` | all | root log level |
| `KPI_DATABASE_URL` | `postgresql+asyncpg://kpi:kpi@localhost:5432/kpi` | all | async SQLAlchemy URL; Alembic derives the sync URL |
| `KPI_CORRELATION_HEADER` | `X-Correlation-Id` | api, mcp | trace id header |
| `KPI_DEFAULT_TENANT_ID` | `default` | all | tenant bound to `RequestContext` |
| `KPI_FUZZY_CUTOFF` | `55` | core | minimum rapidfuzz score for suggestions |
| `KPI_FUZZY_LIMIT` | `5` | core | max suggestions |
| `OTEL_SDK_DISABLED` | `true` | all | set `false` + `OTEL_EXPORTER_OTLP_ENDPOINT` to export traces |
| `KPI_API_HOST` / `KPI_API_PORT` | `0.0.0.0` / `8080` | api | bind |
| `KPI_CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | api | allowlist; `*` rejected in production |
| `KPI_RATE_LIMIT_RPS` / `KPI_RATE_LIMIT_BURST` | `5` / `20` | api | token bucket per client IP |
| `KPI_MAX_BODY_BYTES` | `16384` | api | request body cap |
| `KPI_MCP_URL` | `http://localhost:8090/mcp` | api | MCP endpoint for the agent |
| `KPI_MCP_MODE` | `http` | api | `http` or `inprocess` |
| `KPI_LLM_PROVIDER` | `stub` | api | `stub` or `anthropic` |
| `KPI_LLM_MODEL` | `claude-opus-5` | api | model id |
| `KPI_LLM_EFFORT` | `medium` | api | `low\|medium\|high` |
| `KPI_LLM_MAX_TOKENS` | `8000` | api | per turn |
| `KPI_LLM_TIMEOUT_S` | `60` | api | provider request timeout |
| `KPI_LLM_FALLBACKS` | `off` | api | `default` enables Anthropic server-side refusal fallbacks (beta); off by design |
| `ANTHROPIC_API_KEY` | – | api | required when provider is `anthropic` |
| `KPI_AGENT_MAX_ITERATIONS` | `8` | api | LLM turns per message |
| `KPI_AGENT_MAX_PARALLEL_TOOLS` | `4` | api | tool_use blocks executed per turn |
| `KPI_AGENT_TOOL_TIMEOUT_S` | `10` | api | per tool call |
| `KPI_AGENT_MAX_WALL_CLOCK_S` | `60` | api | per message |
| `KPI_AGENT_MAX_MESSAGE_CHARS` | `4000` | api | user message cap |
| `KPI_AGENT_HISTORY_WINDOW` | `20` | api | prior messages sent to the model |
| `KPI_AGENT_MAX_RESULT_CHARS` | `6000` | api | tool result truncation |
| `KPI_MCP_TRANSPORT` | `http` | mcp | `stdio` or `http` |
| `KPI_MCP_HOST` / `KPI_MCP_PORT` | `0.0.0.0` / `8090` | mcp | bind |
| `KPI_MCP_RATE_LIMIT_RPS` / `KPI_MCP_RATE_LIMIT_BURST` | `20` / `40` | mcp | FastMCP rate limiter |
| `KPI_MCP_MAX_HISTORY_POINTS` | `64` | mcp | result cap |
| `VITE_API_BASE_URL` | `/api` | chat-web | build-time API base |
| `VITE_CHAT_URL` | `links.chatUrl` | website | chat CTA target; empty hides every chat link |
| `VITE_API_DOCS_URL` | `links.apiDocsUrl` | website | API docs link; empty hides it |
| `VITE_SITE_URL` | `links.siteUrl` | website | canonical URL, `robots.txt`, `sitemap.xml` |
| `KPI_BRAND_CONFIG` | `./brand.config.json` (searched upwards) | api, mcp, migrate | path of the brand file |
| `BRAND_CONFIG` | `../../brand.config.json` | chat-web, website (build) | path of the brand file |
| `API_UPSTREAM` | `http://api:8080` | chat-web image | where nginx proxies `/api` |
| `KPI_TEST_DATABASE_URL` | – | tests | use an existing Postgres instead of testcontainers |

## White-labelling

Names and contact details live in one file, `brand.config.json` at the repository root:

```json
{
  "brand": "Zairus",
  "product": "Zairus KPI Intelligent Platform",
  "dataProvider": "ZairusData",
  "assistantName": "Zairus KPI assistant",
  "mcpServerName": "zairus-kpi",
  "contact": { "email": "...", "phone": "...", "address": { "street": "...", "city": "...", "region": "...", "postalCode": "...", "country": "..." } },
  "social": { "github": "...", "linkedin": "" },
  "links": { "siteUrl": "...", "chatUrl": "...", "apiDocsUrl": "..." }
}
```

| Consumer | Reads | Uses |
|---|---|---|
| `kpi_core.branding.get_brand()` | `KPI_BRAND_CONFIG`, else the nearest `brand.config.json`, else neutral defaults | API title, agent system prompt, MCP server name and instructions |
| website (Vite alias `@brand`) | build time | logo, copy (`{brand}`, `{product}`, `{provider}` in the message files), contact page, `<title>`/Open Graph tags, robots/sitemap |
| chat-web (Vite alias `@brand`) | build time | header, empty state, `<title>` |

A missing file never breaks the Python services (they fall back to neutral defaults); the web
builds fail fast with a clear message. `scripts/audit_docs.py` fails CI if the brand or provider
name is hard-coded in application source.
