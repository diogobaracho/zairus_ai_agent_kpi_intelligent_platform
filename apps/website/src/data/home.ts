import {
  Activity,
  Bot,
  Database,
  Eye,
  FileSearch,
  ShieldCheck,
  Timer,
  Waypoints,
  type LucideIcon,
} from 'lucide-react';
import type { TraceStep } from '../types/content';

// Copy lives in src/i18n/messages/*.json; these lists only hold ids, icons and numbers.

export const heroBadges = ['estimates', 'toolCalls', 'mcp', 'local'] as const;

export const steps = [
  { number: '01', id: 'ask' },
  { number: '02', id: 'pick' },
  { number: '03', id: 'govern' },
  { number: '04', id: 'evidence' },
] as const;

export const capabilities: { id: string; icon: LucideIcon }[] = [
  { id: 'discovery', icon: FileSearch },
  { id: 'history', icon: Activity },
  { id: 'chat', icon: Bot },
  { id: 'mcp', icon: Waypoints },
  { id: 'rest', icon: Database },
  { id: 'audit', icon: Eye },
];
export const capabilityBullets = ['b1', 'b2', 'b3'] as const;

/** Facts about data/kpi_sample.csv (regenerate with scripts/generate_sample_data.py). */
export const dataset = {
  companies: 16,
  sectors: 14,
  kpis: 13,
  quarters: 14,
  firstQuarter: '2023Q1',
  lastQuarter: '2026Q2',
  qtdQuarter: '2026Q3',
  qtdAsOf: '2026-09-15',
};

export const metrics = [
  { id: 'companies', value: String(dataset.companies), values: { sectors: dataset.sectors } },
  { id: 'kpis', value: String(dataset.kpis), values: {} },
  {
    id: 'quarters',
    value: String(dataset.quarters),
    values: { from: dataset.firstQuarter, to: dataset.lastQuarter },
  },
  { id: 'audited', value: '100%', values: {} },
] as const;

/** Tool timeline shown in the hero mockup; `note` is a message id plus its values. */
export const trace: (TraceStep & { values?: Record<string, string | number> })[] = [
  {
    tool: 'get_kpi_history',
    args: 'ticker=ORBYY kpi=revenue',
    status: 'error',
    ms: 4,
    note: 'mockup.notFound',
  },
  {
    tool: 'get_kpi_history',
    args: 'ticker=ORBY kpi=total_revenue',
    status: 'ok',
    ms: 31,
    note: 'mockup.historyNote',
    values: { count: dataset.quarters, from: dataset.firstQuarter, to: dataset.lastQuarter },
  },
  {
    tool: 'get_kpi_qtd',
    args: 'ticker=ORBY kpi=total_revenue',
    status: 'ok',
    ms: 12,
    note: 'mockup.qtdNote',
    values: { period: dataset.qtdQuarter, asOf: dataset.qtdAsOf },
  },
];

export const guardrails: { id: string; icon: LucideIcon }[] = [
  { id: 'database', icon: ShieldCheck },
  { id: 'recorded', icon: Eye },
  { id: 'budgets', icon: Timer },
  { id: 'recover', icon: Bot },
];
