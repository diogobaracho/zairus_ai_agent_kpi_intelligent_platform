import { describe, expect, it } from 'vitest';
import type { KpiHistory, KpiQtd } from '../../api/types';
import { buildChartRows } from '../../lib/chart';

const company = { ticker: 'ORBY', name: 'Orbitly Analytics', sector: 'Software' };
const kpi = {
  slug: 'total_revenue',
  name: 'Total Revenue ($MM)',
  display_name: 'Total Revenue',
  unit: '$MM',
  unit_kind: 'currency' as const,
  scale: 1e6,
  description: '',
};

describe('buildChartRows', () => {
  it('keeps history as one series and the latest QTD as a separate dashed point', () => {
    const history: KpiHistory = {
      company,
      kpi,
      count: 2,
      truncated: false,
      note: null,
      available_range: null,
      points: [
        {
          period: '2025Q3',
          period_start: '2025-07-01',
          period_end: '2025-09-30',
          value: 900,
          unit: '$MM',
        },
        {
          period: '2026Q2',
          period_start: '2025-10-01',
          period_end: '2025-12-31',
          value: 945.3,
          unit: '$MM',
        },
      ],
    };
    const qtd: KpiQtd = {
      company,
      kpi,
      period: '2026Q3',
      latest: { period: '2026Q3', as_of: '2026-09-15', value: 627.45, unit: '$MM' },
      snapshots: [],
      prior_quarter: null,
      note: null,
    };
    const rows = buildChartRows(history, qtd);
    expect(rows).toHaveLength(3);
    expect(rows[2]).toMatchObject({ period: '2026Q3', qtd: 627.45, as_of: '2026-09-15' });
    expect(rows[2].historical).toBeUndefined();
    expect(buildChartRows(null, null)).toEqual([]);
  });
});
