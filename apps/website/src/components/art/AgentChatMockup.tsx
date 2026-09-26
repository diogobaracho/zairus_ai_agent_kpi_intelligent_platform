import { useIntl } from 'react-intl';
import { dataset, trace } from '../../data/home';
import { useT } from '../../i18n/useT';

const tone = {
  ok: 'bg-green-50 text-green-700',
  error: 'bg-red-50 text-red-700',
  rejected: 'bg-amber-50 text-amber-700',
};

// ORBY total revenue in the generated sample dataset ($MM).
const revenue = { first: 222.97, last: 387.23, qtd: 335.94 };

export default function AgentChatMockup() {
  const t = useT();
  const intl = useIntl();
  const money = (v: number) =>
    `${intl.formatNumber(v, { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })}MM`;
  const growth = intl.formatNumber(revenue.last / revenue.first - 1, {
    style: 'percent',
    maximumFractionDigits: 1,
    signDisplay: 'always',
  });
  return (
    <div
      className="animate-rise rounded-3xl border border-line bg-white p-4 shadow-float md:p-6"
      aria-label={t('mockup.chatLabel')}
    >
      <div className="grid gap-4 md:grid-cols-[1.2fr_1fr]">
        <div className="space-y-3 text-sm">
          <div className="ml-auto max-w-[85%] rounded-2xl bg-brand px-4 py-2 text-white">
            {t('mockup.question')}
          </div>
          <div className="max-w-[92%] rounded-2xl border border-line bg-paper px-4 py-3 text-ink">
            <p>
              <span className="font-semibold">ORBY Total Revenue ($MM)</span>:{' '}
              {t('mockup.answerHistory', {
                from: dataset.firstQuarter,
                first: money(revenue.first),
                to: dataset.lastQuarter,
                last: money(revenue.last),
                count: dataset.quarters,
                growth,
              })}
            </p>
            <p className="mt-1">
              {t('mockup.answerQtd', {
                period: dataset.qtdQuarter,
                asOf: dataset.qtdAsOf,
                value: money(revenue.qtd),
              })}
            </p>
            <p className="mt-2 text-xs text-ink-soft">{t('mockup.answerRecovery')}</p>
          </div>
        </div>
        <div className="rounded-2xl border border-line bg-paper p-3 text-xs">
          <div className="mb-2 flex items-center justify-between font-semibold">
            <span>{t('mockup.toolExecution')}</span>
            <span className="text-ink-soft">{t('mockup.calls', { count: trace.length })}</span>
          </div>
          <ol className="space-y-2">
            {trace.map((step, i) => (
              <li key={i} className="rounded-xl border border-line bg-white p-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold">{step.tool}</span>
                  <span className={`rounded-full px-2 py-0.5 ${tone[step.status]}`}>
                    {step.status}
                  </span>
                  <span className="ml-auto text-ink-soft">{step.ms} ms</span>
                </div>
                <div className="mt-1 font-mono text-[11px] text-ink-soft">{step.args}</div>
                {step.note && (
                  <div className="mt-1 text-[11px] text-ink-soft">{t(step.note, step.values)}</div>
                )}
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
