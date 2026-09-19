import type { UiMessage } from '../../state/chatReducer';
import { ToolCallCard } from './ToolCallCard';
import { TraceLink } from './TraceLink';

export function ToolExecutionPanel({ message }: { message: UiMessage | null }) {
  if (!message) {
    return (
      <aside className="card p-4 text-sm text-ink-soft" aria-label="Tool execution">
        <h2 className="mb-1 font-semibold text-ink">Tool execution</h2>
        Every tool the agent calls appears here with its arguments, status, duration and result.
      </aside>
    );
  }
  const running = message.status === 'streaming';
  return (
    <aside className="card flex flex-col gap-3 p-4" aria-label="Tool execution">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Tool execution</h2>
        <span className="text-xs text-ink-soft">
          {message.steps.length} call{message.steps.length === 1 ? '' : 's'}
        </span>
      </div>
      {message.steps.length === 0 && (
        <p className="text-sm text-ink-soft">
          {running ? 'Thinking…' : 'No tools were called for this answer.'}
        </p>
      )}
      {message.steps.map((step, index) => (
        <ToolCallCard
          key={step.id}
          step={step}
          running={
            running && index === message.steps.length - 1 && step.duration_ms === 0 && !step.error
          }
        />
      ))}
      {message.stoppedReason && message.stoppedReason !== 'end_turn' && (
        <p className="text-xs text-amber-700">Stopped early: {message.stoppedReason}</p>
      )}
      {message.usage && (
        <p className="text-xs text-ink-soft">
          {message.usage.iterations} iteration{message.usage.iterations === 1 ? '' : 's'} ·{' '}
          {message.usage.tool_calls} tool call
          {message.usage.tool_calls === 1 ? '' : 's'} ·{' '}
          {message.usage.input_tokens + message.usage.output_tokens} tokens
        </p>
      )}
      <TraceLink traceId={message.traceId} />
    </aside>
  );
}
