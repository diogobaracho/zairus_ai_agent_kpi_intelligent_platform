export function formatValue(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const abs = Math.abs(value);
  const compact =
    abs >= 1_000_000
      ? `${(value / 1_000_000).toFixed(2)}M`
      : abs >= 10_000
        ? `${(value / 1_000).toFixed(1)}K`
        : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (unit === '%') return `${value.toFixed(1)}%`;
  if (unit === '$') return `$${compact}`;
  if (unit === '$MM') return `$${compact}MM`;
  if (unit === '$B') return `$${compact}B`;
  return `${compact} ${unit}`.trim();
}

export function pctChange(current: number, previous: number): string {
  if (!previous) return '—';
  const pct = ((current - previous) / previous) * 100;
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
}

export function formatDuration(ms: number): string {
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(2)} s`;
}

export function statusTone(status: string): 'ok' | 'warn' | 'bad' | 'muted' {
  if (status === 'ok') return 'ok';
  if (status === 'rejected') return 'warn';
  if (status === 'error' || status === 'timeout') return 'bad';
  return 'muted';
}
