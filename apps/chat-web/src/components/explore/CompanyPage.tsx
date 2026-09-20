import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ProblemError } from '../../api/client';
import { getCompanyKpis, getHistory, getQtd } from '../../api/endpoints';
import type { Company, CompanyKpi, KpiHistory, KpiQtd, Problem } from '../../api/types';
import { formatValue, pctChange } from '../../lib/format';
import { ErrorBanner } from '../chat/ErrorBanner';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { Spinner } from '../ui/Spinner';
import { KpiHistoryChart } from './KpiHistoryChart';

export default function CompanyPage() {
  const { ticker = '' } = useParams();
  const [company, setCompany] = useState<Company | null>(null);
  const [kpis, setKpis] = useState<CompanyKpi[]>([]);
  const [slug, setSlug] = useState<string>('');
  const [history, setHistory] = useState<KpiHistory | null>(null);
  const [qtd, setQtd] = useState<KpiQtd | null>(null);
  const [error, setError] = useState<Problem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getCompanyKpis(ticker)
      .then((r) => {
        setCompany(r.company);
        setKpis(r.items);
        setSlug((current) => current || r.items[0]?.slug || '');
      })
      .catch((e) =>
        setError(
          e instanceof ProblemError
            ? e.problem
            : { title: 'Error', status: 0, detail: String(e), code: 'network_error' },
        ),
      )
      .finally(() => setLoading(false));
  }, [ticker]);

  useEffect(() => {
    if (!slug) return;
    setError(null);
    Promise.all([getHistory(ticker, slug), getQtd(ticker, slug)])
      .then(([h, q]) => {
        setHistory(h);
        setQtd(q);
      })
      .catch((e) =>
        setError(
          e instanceof ProblemError
            ? e.problem
            : { title: 'Error', status: 0, detail: String(e), code: 'network_error' },
        ),
      );
  }, [ticker, slug]);

  if (loading) return <Spinner label="Loading company" />;
  if (error && !company) return <ErrorBanner problem={error} />;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Link to="/explore" className="text-xs text-brand hover:underline">
          ← Explorer
        </Link>
        <h1 className="text-lg font-semibold">
          {company?.name} <span className="font-mono text-sm text-ink-soft">{company?.ticker}</span>
        </h1>
        <div className="text-xs text-ink-soft">{company?.sector}</div>
      </div>
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="KPIs">
        {kpis.map((k) => (
          <button
            key={k.slug}
            role="tab"
            aria-selected={k.slug === slug}
            onClick={() => setSlug(k.slug)}
            className={`rounded-lg border px-3 py-1.5 text-sm ${k.slug === slug ? 'border-brand bg-brand-soft text-brand-dark' : 'border-slate-200 bg-white hover:border-brand'}`}
          >
            {k.display_name} <span className="text-xs text-ink-soft">({k.unit})</span>
            {k.has_qtd && <Badge tone="brand">QTD</Badge>}
          </button>
        ))}
      </div>
      {error && <ErrorBanner problem={error} />}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Card>
          <h2 className="mb-2 text-sm font-semibold">History vs QTD</h2>
          <KpiHistoryChart history={history} qtd={qtd} />
          {history?.note && <p className="mt-2 text-xs text-amber-700">{history.note}</p>}
        </Card>
        <Card>
          <h2 className="text-sm font-semibold">Quarter to date</h2>
          {qtd?.latest ? (
            <div className="mt-2 text-sm">
              <div className="text-2xl font-semibold">
                {formatValue(qtd.latest.value, qtd.latest.unit)}
              </div>
              <div className="text-xs text-ink-soft">
                {qtd.period} · as of {qtd.latest.as_of}
              </div>
              {qtd.prior_quarter && (
                <div className="mt-1 text-xs">
                  vs {qtd.prior_quarter.period}:{' '}
                  {formatValue(qtd.prior_quarter.value, qtd.prior_quarter.unit)} (
                  {pctChange(qtd.latest.value, qtd.prior_quarter.value)})
                </div>
              )}
              <table className="mt-3 w-full text-xs">
                <thead>
                  <tr className="text-left text-ink-soft">
                    <th>as_of</th>
                    <th className="text-right">value</th>
                  </tr>
                </thead>
                <tbody>
                  {qtd.snapshots.map((s) => (
                    <tr key={s.as_of}>
                      <td className="font-mono">{s.as_of}</td>
                      <td className="text-right">{formatValue(s.value, s.unit)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mt-2 text-sm text-ink-soft">{qtd?.note ?? 'No QTD estimate.'}</p>
          )}
        </Card>
      </div>
      {history && history.points.length > 0 && (
        <Card>
          <h2 className="mb-2 text-sm font-semibold">Historical estimates ({history.count})</h2>
          <table className="w-full text-xs" aria-label="History table">
            <thead>
              <tr className="text-left text-ink-soft">
                <th>period</th>
                <th className="text-right">value</th>
                <th className="text-right">QoQ</th>
              </tr>
            </thead>
            <tbody>
              {history.points.map((p, i) => (
                <tr key={p.period} className="border-t border-slate-100">
                  <td className="font-mono">{p.period}</td>
                  <td className="text-right">{formatValue(p.value, p.unit)}</td>
                  <td className="text-right text-ink-soft">
                    {i > 0 ? pctChange(p.value, history.points[i - 1].value) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
