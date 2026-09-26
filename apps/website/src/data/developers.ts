import { brand } from '../brand';
import type { CodeSample, Tool } from '../types/content';

// Tool purposes live in the message files under developers.toolPurpose.<name>; sample titles
// are message ids. Code itself is never translated.

export const tools: Tool[] = [
  {
    name: 'search_companies',
    params: 'query?, sector?, limit',
    returns: 'companies[], total, suggestions[] when empty, sectors_available[]',
  },
  {
    name: 'list_company_kpis',
    params: 'ticker',
    returns: 'company, kpis[] {slug, name, unit, first_period, last_period, has_qtd}',
  },
  {
    name: 'get_kpi_history',
    params: 'ticker, kpi, from_period?, to_period?, limit',
    returns: 'points[] {period, value, unit}, count, available_range, note',
  },
  {
    name: 'get_kpi_qtd',
    params: 'ticker, kpi',
    returns: 'period, latest {as_of, value}, snapshots[], prior_quarter',
  },
];

export const samples: CodeSample[] = [
  {
    title: 'developers.samples.stdio',
    language: 'json',
    code: `{
  "mcpServers": {
    "${brand.mcpServerName}": {
      "command": "uv",
      "args": ["run", "--project", "services/mcp", "python", "-m", "kpi_mcp", "--transport", "stdio"],
      "cwd": "/path/to/your/checkout",
      "env": { "KPI_DATABASE_URL": "postgresql+asyncpg://kpi:kpi@localhost:5432/kpi" }
    }
  }
}`,
  },
  {
    title: 'developers.samples.http',
    language: 'json',
    code: `{ "mcpServers": { "${brand.mcpServerName}": { "url": "http://localhost:8090/mcp" } } }`,
  },
  {
    title: 'developers.samples.rest',
    language: 'bash',
    code: `curl -s "http://localhost:8080/v1/companies?q=orbitly" | jq '.items[0]'
curl -s http://localhost:8080/v1/companies/ORBY/kpis/total_revenue/qtd | jq '.latest'
curl -N -X POST http://localhost:8080/v1/chat -H 'content-type: application/json' \\
  -d '{"message":"What is ORBY total revenue QTD?"}'      # server-sent events`,
  },
  {
    title: 'developers.samples.envelope',
    language: 'json',
    code: `{"error": {"code": "kpi_not_found",
  "message": "KPI 'Totl Revenue' not found for ORBY",
  "suggestions": [{"value": "total_revenue", "label": "Total Revenue ($MM)", "score": 95.2}],
  "recovery_hint": "Retry with kpi set to suggestions[0].value, or call list_company_kpis.",
  "retryable": true, "trace_id": "9f1c2ab4d0e3f5a7"}}`,
  },
];

export const quickstart = [
  'git clone <repo> && cd <repo>',
  'make bootstrap',
  'make up        # postgres, migrations, seed, api, mcp, chat, website',
  'open http://localhost:3000',
];
