import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { KpiHistory, KpiQtd } from '../../api/types';
import { buildChartRows, type ChartRow } from '../../lib/chart';
import { formatValue } from '../../lib/format';

export function KpiHistoryChart({
  history,
  qtd,
}: {
  history: KpiHistory | null;
  qtd: KpiQtd | null;
}) {
  const rows = buildChartRows(history, qtd);
  const unit = rows[0]?.unit ?? '';
  if (rows.length === 0) return <p className="text-sm text-ink-soft">No data to chart.</p>;
  return (
    <div className="h-72 w-full" data-testid="kpi-chart" data-points={rows.length}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" />
          <XAxis dataKey="period" tick={{ fontSize: 11 }} />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => formatValue(v, unit)}
            width={80}
          />
          <Tooltip
            formatter={(value: number, name: string, item: { payload?: ChartRow }) => [
              formatValue(value, unit),
              name === 'qtd' ? `QTD (as of ${item.payload?.as_of ?? '?'})` : 'Historical',
            ]}
          />
          <Line
            type="monotone"
            dataKey="historical"
            name="historical"
            stroke="#2F6BFF"
            strokeWidth={2}
            dot={{ r: 3 }}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="qtd"
            name="qtd"
            stroke="#F59E0B"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
