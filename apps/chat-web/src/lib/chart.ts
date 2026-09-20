import type { KpiHistory, KpiQtd } from '../api/types';

export interface ChartRow {
  period: string;
  historical?: number;
  qtd?: number;
  as_of?: string;
  unit: string;
}

/** Historical points as one series; the latest QTD snapshot as a separate series on its own quarter. */
export function buildChartRows(history: KpiHistory | null, qtd: KpiQtd | null): ChartRow[] {
  const rows: ChartRow[] = (history?.points ?? []).map((p) => ({
    period: p.period,
    historical: p.value,
    unit: p.unit,
  }));
  if (qtd?.latest) {
    const existing = rows.find((r) => r.period === qtd.latest!.period);
    if (existing) {
      existing.qtd = qtd.latest.value;
      existing.as_of = qtd.latest.as_of;
    } else {
      rows.push({
        period: qtd.latest.period,
        qtd: qtd.latest.value,
        as_of: qtd.latest.as_of,
        unit: qtd.latest.unit,
      });
    }
  }
  return rows;
}
