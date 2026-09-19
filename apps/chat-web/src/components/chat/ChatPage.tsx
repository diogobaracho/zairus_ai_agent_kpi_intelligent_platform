import { useEffect, useMemo, useRef, useState } from 'react';
import { RotateCcw } from 'lucide-react';
import { useChat } from '../../state/useChat';
import { ToolExecutionPanel } from '../tools/ToolExecutionPanel';
import { Button } from '../ui/Button';
import { Composer } from './Composer';
import { EmptyState } from './EmptyState';
import { ErrorBanner } from './ErrorBanner';
import { MessageBubble } from './MessageBubble';

export default function ChatPage() {
  const { state, send, stop, reset } = useChat();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastAssistant = useMemo(
    () => [...state.messages].reverse().find((m) => m.role === 'assistant') ?? null,
    [state.messages],
  );
  const selected =
    state.messages.find((m) => m.id === selectedId && m.role === 'assistant') ?? lastAssistant;
  const lastUser = [...state.messages].reverse().find((m) => m.role === 'user');

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages.length, lastAssistant?.content]);

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section className="flex min-h-[70vh] flex-col gap-3" aria-label="Chat">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold">Chat</h1>
          {state.messages.length > 0 && (
            <Button variant="ghost" onClick={reset} aria-label="New chat">
              <RotateCcw className="h-4 w-4" /> New chat
            </Button>
          )}
        </div>
        {state.messages.length === 0 && <EmptyState onPick={(q) => void send(q)} />}
        <div className="flex flex-1 flex-col gap-3" aria-live="polite">
          {state.messages.map((m) => (
            <MessageBubble
              key={m.id}
              message={m}
              selected={selected?.id === m.id}
              onSelect={() => m.role === 'assistant' && setSelectedId(m.id)}
            />
          ))}
          {state.status === 'streaming' && (
            <div className="text-xs text-ink-soft" role="status">
              Working… tool calls appear on the right as they happen.
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        {state.error && (
          <ErrorBanner
            problem={state.error}
            onRetry={lastUser ? () => void send(lastUser.content) : undefined}
          />
        )}
        <Composer onSend={(t) => void send(t)} onStop={stop} busy={state.status === 'streaming'} />
      </section>
      <ToolExecutionPanel message={selected} />
    </div>
  );
}
