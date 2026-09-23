import type { Metric } from '../types/content';

export const layers = [
  {
    name: 'Clients',
    items: [
      'Chat web app (React)',
      'Claude Desktop, Cursor and other MCP clients',
      'Dashboards and scripts over REST',
    ],
  },
  {
    name: 'Adapters',
    items: [
      'REST API: FastAPI, problem+json, rate limits',
      'MCP server: FastMCP, 4 tools, audit middleware',
      'Chat agent: guarded tool loop, SSE streaming',
    ],
  },
  {
    name: 'Domain',
    items: [
      'One service layer shared by both adapters',
      'Validation, suggestions and error semantics defined once',
      'RequestContext carries tenant, principal and trace id',
    ],
  },
  {
    name: 'Data',
    items: [
      'Postgres 16 with functional and partial indexes',
      'Idempotent ingestion of KPI estimates',
      'Audit table for tool calls; persisted conversations',
    ],
  },
];

export const tenancy = [
  'Identity comes from the server, never from the model: tool schemas have no tenant or user fields.',
  'A RequestContext travels with every service call, so per-tenant row-level security is a column and a policy away.',
  'Every audit row already stores the tenant id and the trace id.',
];

export const observability: Metric[] = [
  {
    value: '1',
    label: 'trace id',
    detail: "from the browser to the audit row and both services' logs",
  },
  {
    value: '6',
    label: 'fields per tool call',
    detail: 'tool, arguments, duration, status, error, trace id',
  },
  {
    value: '2',
    label: 'health endpoints',
    detail: 'liveness and readiness with dependency checks',
  },
];
