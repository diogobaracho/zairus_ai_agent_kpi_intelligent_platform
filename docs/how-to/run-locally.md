# Run the stack locally

Prerequisites: Docker with Compose v2, `uv` ≥ 0.12, Node ≥ 20 with corepack (`.tool-versions`
pins Node 24.21). No API keys are needed.

1. Clone and enter the repository.
2. `make bootstrap` — installs Python packages (`uv sync --all-packages`) and JS packages
   (`corepack enable && pnpm install`), then runs `scripts/doctor.sh`.
3. `cp .env.example .env` (optional; defaults work).
4. `make up` — starts Postgres, runs migrations and the seed once, then API (`:8080`), MCP
   (`:8090`), chat-web (`:3000`) and website (`:3001`).
5. `make seed-demo` — optional demo companies `GAPW`, `SPRW`, `FRSH` for edge-case demos.
6. Open <http://localhost:3000> and ask: *What's ORBY's QTD total revenue this quarter?*

Dev mode without containers for one service: `make api` (uvicorn reload), `make mcp-http`,
`make web` (Vite on `:5173`, proxying `/api` to `:8080`), `make website`.

To use a real model: set `KPI_LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=…` in `.env`, then
`make up` again. The provider and model appear in the chat header and in the SSE `session` event.

## Verify

```bash
curl -s localhost:8080/readyz
# {"status":"ok","checks":{"db":"ok","mcp":"ok","llm_provider":"stub"}}
curl -s 'localhost:8080/v1/companies?q=orbitly' | jq '.items[0].ticker'
# "ORBY"
```

## What usually goes wrong

- **Port in use**: change `KPI_API_PORT`/`KPI_MCP_PORT` or stop the other process.
- **`make up` hangs on migrate**: Postgres not healthy yet; `docker compose logs postgres`.
- **pnpm not found**: `corepack enable` (Node ships corepack); `.tool-versions` needs asdf/mise.
- **Chat answers look scripted**: that is the stub provider; set the Anthropic variables.
