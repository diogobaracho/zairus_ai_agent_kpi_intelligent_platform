import { AlertTriangle } from 'lucide-react';
import type { Problem } from '../../api/types';

export function ErrorBanner({ problem, onRetry }: { problem: Problem; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800"
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">
        <div className="font-semibold">
          {problem.title} <span className="font-mono text-xs">({problem.code})</span>
        </div>
        <div>{problem.detail}</div>
        {problem.recovery_hint && <div className="mt-1 italic">{problem.recovery_hint}</div>}
        {problem.trace_id && <div className="mt-1 font-mono text-xs">trace {problem.trace_id}</div>}
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-lg border border-red-300 px-2 py-1 text-xs hover:bg-red-100"
        >
          Retry
        </button>
      )}
    </div>
  );
}
