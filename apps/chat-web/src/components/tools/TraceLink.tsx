import { Link } from 'react-router-dom';
import { Copy, Search } from 'lucide-react';

export function TraceLink({ traceId }: { traceId?: string }) {
  if (!traceId) return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs text-ink-soft">
      <span className="font-mono">trace {traceId}</span>
      <button
        type="button"
        className="rounded p-0.5 hover:bg-slate-100"
        title="Copy trace id"
        aria-label="Copy trace id"
        onClick={() => navigator.clipboard?.writeText(traceId)}
      >
        <Copy className="h-3 w-3" />
      </button>
      <Link
        to={`/trace/${traceId}`}
        className="inline-flex items-center gap-1 text-brand hover:underline"
        title="Open audit trail"
      >
        <Search className="h-3 w-3" /> audit
      </Link>
    </span>
  );
}
