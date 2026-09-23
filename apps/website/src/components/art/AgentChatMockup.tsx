import { trace } from '../../data/home';

const tone = {
  ok: 'bg-green-50 text-green-700',
  error: 'bg-red-50 text-red-700',
  rejected: 'bg-amber-50 text-amber-700',
};

export default function AgentChatMockup() {
  return (
    <div
      className="animate-rise rounded-3xl border border-line bg-white p-4 shadow-float md:p-6"
      aria-label="Chat mockup"
    >
      <div className="grid gap-4 md:grid-cols-[1.2fr_1fr]">
        <div className="space-y-3 text-sm">
          <div className="ml-auto max-w-[85%] rounded-2xl bg-brand px-4 py-2 text-white">
            Show ORBYY revenue history and the current quarter
          </div>
          <div className="max-w-[92%] rounded-2xl border border-line bg-paper px-4 py-3 text-ink">
            <p>
              <span className="font-semibold">ORBY Total Revenue ($MM)</span>: 2023Q1 = $222.97MM …
              2026Q2 = $387.23MM (14 quarters, +73.7% overall).
            </p>
            <p className="mt-1">
              QTD 2026Q3 as of <span className="font-mono">2026-09-15</span>: $335.94MM.
            </p>
            <p className="mt-2 text-xs text-ink-soft">
              I first tried ticker ORBYY, which does not exist; the tool suggested ORBY.
            </p>
          </div>
        </div>
        <div className="rounded-2xl border border-line bg-paper p-3 text-xs">
          <div className="mb-2 flex items-center justify-between font-semibold">
            <span>Tool execution</span>
            <span className="text-ink-soft">{trace.length} calls</span>
          </div>
          <ol className="space-y-2">
            {trace.map((t, i) => (
              <li key={i} className="rounded-xl border border-line bg-white p-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold">{t.tool}</span>
                  <span className={`rounded-full px-2 py-0.5 ${tone[t.status]}`}>{t.status}</span>
                  <span className="ml-auto text-ink-soft">{t.ms} ms</span>
                </div>
                <div className="mt-1 font-mono text-[11px] text-ink-soft">{t.args}</div>
                {t.note && <div className="mt-1 text-[11px] text-ink-soft">{t.note}</div>}
              </li>
            ))}
          </ol>
          <div className="mt-2 font-mono text-[10px] text-ink-soft">
            trace 9f1c2ab4d0e3f5a7 · audit ↗
          </div>
        </div>
      </div>
    </div>
  );
}
