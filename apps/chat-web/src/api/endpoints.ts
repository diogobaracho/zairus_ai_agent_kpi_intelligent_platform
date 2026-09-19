import { fetchJson } from './client';
import type {
  Company,
  CompanyKpi,
  Conversation,
  KpiHistory,
  KpiQtd,
  Sector,
  ToolCallAudit,
} from './types';

export const getSectors = () => fetchJson<{ items: Sector[] }>('/v1/sectors');
export const searchCompanies = (q?: string, sector?: string) => {
  const params = new URLSearchParams({ limit: '100' });
  if (q) params.set('q', q);
  if (sector) params.set('sector', sector);
  return fetchJson<{
    items: Company[];
    total: number;
    suggestions: { value: string; label: string }[];
  }>(`/v1/companies?${params}`);
};
export const getCompanyKpis = (ticker: string) =>
  fetchJson<{ company: Company; items: CompanyKpi[] }>(
    `/v1/companies/${encodeURIComponent(ticker)}/kpis`,
  );
export const getHistory = (ticker: string, kpi: string) =>
  fetchJson<KpiHistory>(
    `/v1/companies/${encodeURIComponent(ticker)}/kpis/${encodeURIComponent(kpi)}/history`,
  );
export const getQtd = (ticker: string, kpi: string) =>
  fetchJson<KpiQtd>(
    `/v1/companies/${encodeURIComponent(ticker)}/kpis/${encodeURIComponent(kpi)}/qtd`,
  );
export const getConversation = (id: string) =>
  fetchJson<Conversation>(`/v1/chat/conversations/${encodeURIComponent(id)}`);
export const getAudit = (traceId: string) =>
  fetchJson<{ items: ToolCallAudit[] }>(
    `/v1/audit/tool-calls?trace_id=${encodeURIComponent(traceId)}&limit=200`,
  );
