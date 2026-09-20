import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ProblemError } from '../../api/client';
import { getAudit } from '../../api/endpoints';
import type { Problem, ToolCallAudit } from '../../api/types';
import { formatDuration, statusTone } from '../../lib/format';
import { ErrorBanner } from '../chat/ErrorBanner';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { Spinner } from '../ui/Spinner';

export default function TracePage() {
  const { traceId = '' } = useParams();
  const [rows, setRows] = useState<ToolCallAudit[] | null>(null);
  const [error, setError] = useState<Problem | null>(null);

  useEffect(() => {
    getAudit(traceId)
      .then((r) => setRows(r.items))
      .catch((e) =>
        setError(
          e instanceof ProblemError
            ? e.problem
            : { title: 'Error', status: 0, detail: String(e), code: 'network_error' },
        ),
      );
  }, [traceId]);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Link to="/chat" className="text-xs text-brand hover:underline">
          ← Chat
        </Link>
        <h1 className="text-lg font-semibold">
          Audit trail <span className="font-mono text-sm text-ink-soft">{traceId}</span>
        </h1>
        <p className="text-xs text-ink-soft">
          Every MCP tool call recorded by the server for this trace id.
        </p>
      </div>
      {error && <ErrorBanner problem={error} />}
      {!rows && !error && <Spinner label="Loading audit rows" />}
      {rows && (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-xs" aria-label="Audit rows">
            <thead className="bg-slate-50 text-left text-ink-soft">
              <tr>
                <th className="p-2">time</th>
                <th className="p-2">tool</th>
                <th className="p-2">arguments</th>
                <th className="p-2">status</th>
                <th className="p-2 text-right">duration</th>
                <th className="p-2">caller</th>
                <th className="p-2">error / summary</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-3 text-ink-soft">
                    No audit rows for this trace id.
                  </td>
                </tr>
              )}
              {rows.map((r) => (
                <tr
                  key={r.id ?? `${r.tool_name}-${r.created_at}`}
                  className="border-t border-slate-100 align-top"
                >
                  <td className="p-2 font-mono">{r.created_at?.replace('T', ' ').slice(0, 19)}</td>
                  <td className="p-2 font-mono font-semibold">{r.tool_name}</td>
                  <td className="p-2 font-mono">{JSON.stringify(r.arguments)}</td>
                  <td className="p-2">
                    <Badge tone={statusTone(r.status)}>{r.status}</Badge>
                  </td>
                  <td className="p-2 text-right">{formatDuration(r.duration_ms)}</td>
                  <td className="p-2">
                    {r.caller}
                    {r.transport ? ` · ${r.transport}` : ''}
                  </td>
                  <td className="p-2">
                    {r.error ? (
                      <span className="text-red-700">
                        {r.error.code}: {r.error.message}
                      </span>
                    ) : (
                      r.result_summary
                    )}
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
