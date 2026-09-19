import { useState } from 'react';
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Loader2,
  ShieldAlert,
  XCircle,
} from 'lucide-react';
import type { Step } from '../../api/types';
import { formatDuration, statusTone } from '../../lib/format';
import { Badge } from '../ui/Badge';

function StatusIcon({ status, running }: { status: string; running: boolean }) {
  if (running) return <Loader2 className="h-4 w-4 animate-spin text-brand" aria-label="running" />;
  if (status === 'ok') return <CheckCircle2 className="h-4 w-4 text-mint" aria-label="ok" />;
  if (status === 'rejected')
    return <ShieldAlert className="h-4 w-4 text-amber" aria-label="rejected" />;
  if (status === 'timeout') return <Clock className="h-4 w-4 text-rose" aria-label="timeout" />;
  return <XCircle className="h-4 w-4 text-rose" aria-label="error" />;
}

const whyRejected: Record<string, string> = {
  unknown_tool:
    'The model asked for a tool that does not exist; the call was refused before reaching the server.',
  invalid_tool_input: 'The model produced unparseable tool input; nothing was executed.',
  repeated_failing_call:
    'The model repeated a call that already failed; the loop refused to run it again.',
  repeated_identical_call:
    'The model repeated an identical successful call; refused to avoid a loop.',
  validation_error:
    'The server rejected the arguments (unknown keys, oversized or malformed values).',
};

export function ToolCallCard({ step, running = false }: { step: Step; running?: boolean }) {
  const [open, setOpen] = useState(false);
  const tone = running ? 'muted' : statusTone(step.status);
  const error = step.error;
  return (
    <div className="card p-3 text-sm" data-testid="tool-call-card">
      <button
        type="button"
        className="flex w-full items-center gap-2 text-left"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {open ? (
          <ChevronDown className="h-4 w-4 text-ink-soft" />
        ) : (
          <ChevronRight className="h-4 w-4 text-ink-soft" />
        )}
        <StatusIcon status={step.status} running={running} />
        <span className="font-mono font-semibold">{step.tool}</span>
        <Badge tone={tone}>{running ? 'running' : step.status}</Badge>
        {!running && (
          <span className="ml-auto text-xs text-ink-soft">{formatDuration(step.duration_ms)}</span>
        )}
      </button>
      <div className="mt-2 flex flex-wrap gap-1" aria-label="arguments">
        {Object.entries(step.arguments ?? {}).map(([k, v]) => (
          <span key={k} className="chip">
            {k}={String(v)}
          </span>
        ))}
        {Object.keys(step.arguments ?? {}).length === 0 && (
          <span className="chip">no arguments</span>
        )}
      </div>
      {error && (
        <div
          className="mt-2 rounded-lg border border-red-100 bg-red-50 p-2 text-xs text-red-800"
          role="note"
        >
          <div>
            <span className="font-mono font-semibold">{error.code}</span>: {error.message}
          </div>
          {whyRejected[error.code] && (
            <div className="mt-1 text-red-700">{whyRejected[error.code]}</div>
          )}
          {error.suggestions && error.suggestions.length > 0 && (
            <div className="mt-1 flex flex-wrap items-center gap-1">
              <span>suggestions:</span>
              {error.suggestions.slice(0, 5).map((s) => (
                <span key={s.value} className="chip" title={s.label}>
                  {s.value}
                </span>
              ))}
            </div>
          )}
          {error.recovery_hint && <div className="mt-1 italic">{error.recovery_hint}</div>}
        </div>
      )}
      {open && !running && (
        <pre
          className="mt-2 max-h-48 overflow-auto rounded-lg bg-slate-50 p-2 font-mono text-xs text-ink-soft"
          data-testid="result-preview"
        >
          {step.result_preview || '(no result)'}
        </pre>
      )}
    </div>
  );
}
