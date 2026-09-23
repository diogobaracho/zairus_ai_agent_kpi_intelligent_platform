import type { Metric } from '../../types/content';

export default function MetricStat({
  value,
  label,
  detail,
  dark = false,
}: Metric & { dark?: boolean }) {
  return (
    <div
      className={`rounded-2xl p-6 ${dark ? 'bg-white/5 text-white' : 'border border-line bg-white text-ink'}`}
    >
      <div className="font-display text-4xl font-bold text-brand md:text-5xl">{value}</div>
      <div className="mt-2 font-semibold">{label}</div>
      <div className={`mt-1 text-sm ${dark ? 'text-white/70' : 'text-ink-soft'}`}>{detail}</div>
    </div>
  );
}
