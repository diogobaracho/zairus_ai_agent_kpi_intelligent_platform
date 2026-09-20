import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ProblemError } from '../../api/client';
import { getSectors, searchCompanies } from '../../api/endpoints';
import type { Company, Problem, Sector } from '../../api/types';
import { ErrorBanner } from '../chat/ErrorBanner';
import { Card } from '../ui/Card';
import { Spinner } from '../ui/Spinner';

export default function ExplorePage() {
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [sector, setSector] = useState<string>('');
  const [query, setQuery] = useState('');
  const [companies, setCompanies] = useState<Company[]>([]);
  const [suggestions, setSuggestions] = useState<{ value: string; label: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Problem | null>(null);

  useEffect(() => {
    getSectors()
      .then((r) => setSectors(r.items))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    const handle = setTimeout(() => {
      setLoading(true);
      setError(null);
      searchCompanies(query || undefined, sector || undefined)
        .then((r) => {
          setCompanies(r.items);
          setSuggestions(r.suggestions ?? []);
        })
        .catch((e) =>
          setError(
            e instanceof ProblemError
              ? e.problem
              : { title: 'Error', status: 0, detail: String(e), code: 'network_error' },
          ),
        )
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(handle);
  }, [query, sector]);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold">Explorer</h1>
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor="q" className="sr-only">
          Search companies
        </label>
        <input
          id="q"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ticker or company name"
          className="w-64 rounded-lg border border-slate-200 px-3 py-2 text-sm"
        />
        <label htmlFor="sector" className="sr-only">
          Sector
        </label>
        <select
          id="sector"
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
        >
          <option value="">All sectors ({sectors.reduce((n, s) => n + s.company_count, 0)})</option>
          {sectors.map((s) => (
            <option key={s.name} value={s.name}>
              {s.name} ({s.company_count})
            </option>
          ))}
        </select>
        {loading && <Spinner label="Searching" />}
      </div>
      {error && <ErrorBanner problem={error} />}
      {!loading && companies.length === 0 && !error && (
        <Card className="text-sm text-ink-soft">
          No company matched.
          {suggestions.length > 0 && (
            <span>
              {' '}
              Did you mean:{' '}
              {suggestions.map((s) => (
                <Link
                  key={s.value}
                  to={`/explore/${s.value}`}
                  className="ml-1 text-brand hover:underline"
                >
                  {s.value}
                </Link>
              ))}
              ?
            </span>
          )}
        </Card>
      )}
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" aria-label="Companies">
        {companies.map((c) => (
          <li key={c.ticker}>
            <Link to={`/explore/${c.ticker}`} className="card block p-4 hover:border-brand">
              <div className="font-mono text-xs text-ink-soft">{c.ticker}</div>
              <div className="font-semibold">{c.name}</div>
              <div className="text-xs text-ink-soft">{c.sector}</div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
