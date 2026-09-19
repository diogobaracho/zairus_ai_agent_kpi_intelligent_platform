import type { UiMessage } from '../../state/chatReducer';
import { Badge } from '../ui/Badge';

export function MessageBubble({
  message,
  selected,
  onSelect,
}: {
  message: UiMessage;
  selected: boolean;
  onSelect: () => void;
}) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <button
        type="button"
        onClick={onSelect}
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-left text-sm shadow-sm ${
          isUser
            ? 'bg-brand text-white'
            : `bg-white border ${selected ? 'border-brand' : 'border-slate-200'}`
        }`}
        aria-label={isUser ? 'Your message' : 'Assistant answer'}
      >
        {message.content ||
          (message.status === 'streaming' ? <span className="text-ink-soft">…</span> : '')}
        {message.status === 'error' && message.error && (
          <div className="mt-2">
            <Badge tone="bad">{message.error.code}</Badge>
          </div>
        )}
        {!isUser && message.steps.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.steps.map((s) => (
              <span
                key={s.id}
                className={`chip ${s.status === 'ok' ? '' : 'border-amber-200 bg-amber-50 text-amber-800'}`}
              >
                {s.tool}
              </span>
            ))}
          </div>
        )}
      </button>
    </div>
  );
}
