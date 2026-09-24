import {
  Activity,
  Bot,
  Database,
  Eye,
  FileSearch,
  ShieldCheck,
  Timer,
  Waypoints,
} from 'lucide-react';
import { brand } from '../brand';
import type { Capability, Guardrail, Metric, Step, TraceStep } from '../types/content';

export const hero = {
  eyebrow: 'For public investors and their AI agents',
  title: 'Ask your KPI data. Get answers you can audit.',
  description: `${brand.brand} turns ${brand.dataProvider}'s quarterly KPI estimates into answers: historical trends, the current quarter-to-date estimate, and a visible record of every tool the assistant used to get there.`,
  primaryCta: 'Open the chat demo',
  secondaryCta: 'Connect your AI client',
  badges: [
    'Historical + QTD estimates',
    'Every tool call shown',
    'MCP server for Claude Desktop & Cursor',
    'Runs locally in one command',
  ],
};

export const steps: Step[] = [
  {
    number: '01',
    title: 'Ask in plain language',
    description:
      '"What\'s ORBY\'s ARR doing this quarter?" No tickers or KPI codes required; the assistant finds them.',
  },
  {
    number: '02',
    title: 'The agent picks a tool',
    description:
      'Four read-only MCP tools cover discovery, KPI catalogues, history and quarter-to-date estimates. Wrong guesses come back with suggestions.',
  },
  {
    number: '03',
    title: 'Governed data answers',
    description:
      'Tools call one domain layer over Postgres. The model never sees SQL, ids or tenants; only validated, structured results.',
  },
  {
    number: '04',
    title: 'You see the evidence',
    description:
      'The answer cites ticker, KPI, unit, period and as_of date, and the panel shows each call with arguments, status and duration.',
  },
];

export const capabilities: Capability[] = [
  {
    icon: FileSearch,
    title: 'Company & KPI discovery',
    bullets: [
      'Search by ticker, partial name or sector',
      'Normalised KPI metadata: slug, unit, coverage',
      'Misspellings answered with suggestions',
    ],
  },
  {
    icon: Activity,
    title: 'History vs quarter-to-date',
    bullets: [
      'Chronological completed quarters',
      'QTD snapshots with as_of dates, kept separate',
      'Prior-quarter comparison built in',
    ],
  },
  {
    icon: Bot,
    title: 'Explainable chat',
    bullets: [
      'Streams the answer as it forms',
      'Tool timeline with arguments and results',
      'Failures surfaced, never hidden',
    ],
  },
  {
    icon: Waypoints,
    title: 'MCP server for agents',
    bullets: [
      'Four self-describing tools',
      'stdio for Claude Desktop & Cursor, HTTP for services',
      'Same audit trail for every caller',
    ],
  },
  {
    icon: Database,
    title: 'REST API for products',
    bullets: [
      'Typed, validated JSON',
      'Consistent problem+json errors with hints',
      'OpenAPI document included',
    ],
  },
  {
    icon: Eye,
    title: 'Audit everything',
    bullets: [
      'One trace id from browser to database row',
      'Tool name, arguments, duration, status, error',
      'Reconstruct any answer afterwards',
    ],
  },
];

export const metrics: Metric[] = [
  { value: '16', label: 'companies', detail: 'across 14 sectors in the sample dataset' },
  {
    value: '13',
    label: 'KPIs',
    detail: 'revenue, ARR, retention, churn, GMV, users and more',
  },
  {
    value: '14',
    label: 'quarters of history',
    detail: '2023Q1 to 2026Q2, plus QTD snapshots',
  },
  {
    value: '100%',
    label: 'tool calls audited',
    detail: 'tool, arguments, duration, status, trace id',
  },
];

export const trace: TraceStep[] = [
  {
    tool: 'get_kpi_history',
    args: 'ticker=ORBYY kpi=revenue',
    status: 'error',
    ms: 4,
    note: 'company_not_found → suggestion: ORBY',
  },
  {
    tool: 'get_kpi_history',
    args: 'ticker=ORBY kpi=total_revenue',
    status: 'ok',
    ms: 31,
    note: '14 quarters, 2023Q1..2026Q2',
  },
  {
    tool: 'get_kpi_qtd',
    args: 'ticker=ORBY kpi=total_revenue',
    status: 'ok',
    ms: 12,
    note: '2026Q3 as of 2026-09-15',
  },
];

export const guardrails: Guardrail[] = [
  {
    icon: ShieldCheck,
    title: 'The model never touches the database',
    description:
      'Answers come only through four typed, read-only tools. No SQL, no ids, no tenant fields in any schema.',
  },
  {
    icon: Eye,
    title: 'Every call is recorded',
    description:
      'A trace id follows the request from the browser to the audit row and the logs of both services.',
  },
  {
    icon: Timer,
    title: 'Budgets and timeouts',
    description:
      'Iteration caps, per-tool timeouts, duplicate-call detection and result size limits stop runaway loops.',
  },
  {
    icon: Bot,
    title: 'Errors an agent can recover from',
    description:
      'Structured envelopes with suggestions and a recovery hint turn a typo into one retry, not a failure.',
  },
];

export const finalCta = {
  title: 'See every step behind the answer.',
  description:
    'Start the stack locally with one command, ask a question in the chat, or point Claude Desktop at the MCP server.',
  primary: 'Open the chat demo',
  secondary: 'Read the developer guide',
};
