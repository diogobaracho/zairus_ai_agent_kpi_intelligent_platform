// Mirrors the REST and SSE JSON contracts (docs/reference/rest-api.md, sse-protocol.md).
export interface Problem {
  type?: string;
  title: string;
  status: number;
  detail: string;
  code: string;
  suggestions?: Suggestion[];
  recovery_hint?: string;
  trace_id?: string | null;
}
export interface Suggestion {
  value: string;
  label: string;
  score: number;
}
export interface Company {
  ticker: string;
  name: string;
  sector: string;
}
export interface Sector {
  name: string;
  company_count: number;
}
export interface KpiDefinition {
  slug: string;
  name: string;
  display_name: string;
  unit: string;
  unit_kind: 'currency' | 'count' | 'percent';
  scale: number;
  description: string;
}
export interface CompanyKpi extends KpiDefinition {
  first_period: string | null;
  last_period: string | null;
  historical_count: number;
  has_qtd: boolean;
  latest_qtd_as_of: string | null;
}
export interface KpiPoint {
  period: string;
  period_start: string;
  period_end: string;
  value: number;
  unit: string;
}
export interface QtdSnapshot {
  period: string;
  as_of: string;
  value: number;
  unit: string;
}
export interface KpiHistory {
  company: Company;
  kpi: KpiDefinition;
  points: KpiPoint[];
  count: number;
  truncated: boolean;
  note: string | null;
  available_range: { from_period: string | null; to_period: string | null } | null;
}
export interface KpiQtd {
  company: Company;
  kpi: KpiDefinition;
  period: string | null;
  latest: QtdSnapshot | null;
  snapshots: QtdSnapshot[];
  prior_quarter: KpiPoint | null;
  note: string | null;
}
export type StepStatus = 'ok' | 'error' | 'timeout' | 'rejected';
export interface StepError {
  code: string;
  message: string;
  suggestions?: Suggestion[];
  recovery_hint?: string | null;
  [k: string]: unknown;
}
export interface Step {
  id: string;
  tool: string;
  arguments: Record<string, unknown>;
  iteration: number;
  status: StepStatus;
  duration_ms: number;
  result_preview: string;
  error: StepError | null;
}
export interface SessionData {
  conversation_id: string;
  trace_id: string;
  provider: string;
  model: string;
}
export interface FinalData {
  message_id: string;
  answer: string;
  steps: Step[];
  usage: { input_tokens: number; output_tokens: number; iterations: number; tool_calls: number };
  stopped_reason: string;
}
export interface ErrorData {
  code: string;
  message: string;
  trace_id: string;
  steps: Step[];
}
export type SseEvent =
  | { event: 'session'; data: SessionData }
  | { event: 'text_delta'; data: { delta: string } }
  | {
      event: 'tool_call_started';
      data: { id: string; tool: string; arguments: Record<string, unknown>; iteration: number };
    }
  | { event: 'tool_call_finished'; data: Step }
  | { event: 'final'; data: FinalData }
  | { event: 'error'; data: ErrorData };
export interface ConversationMessage {
  id: string;
  seq: number;
  role: 'user' | 'assistant';
  content: string;
  steps: Step[];
  usage: Record<string, number> | null;
  trace_id: string;
  stopped_reason: string | null;
  created_at: string | null;
}
export interface Conversation {
  id: string;
  title: string | null;
  messages: ConversationMessage[];
}
export interface ToolCallAudit {
  id: number | null;
  trace_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  status: StepStatus;
  duration_ms: number;
  error: StepError | null;
  result_summary: string | null;
  caller: string;
  transport: string | null;
  created_at: string | null;
}
