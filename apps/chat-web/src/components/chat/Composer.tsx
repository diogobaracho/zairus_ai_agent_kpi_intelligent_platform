import { useState, type FormEvent, type KeyboardEvent } from 'react';
import { Send, Square } from 'lucide-react';
import { Button } from '../ui/Button';

const MAX = 4000;

export function Composer({
  onSend,
  onStop,
  busy,
}: {
  onSend: (text: string) => void;
  onStop: () => void;
  busy: boolean;
}) {
  const [text, setText] = useState('');
  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    onSend(trimmed);
    setText('');
  };
  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) submit();
  };
  return (
    <form onSubmit={submit} className="card flex items-end gap-2 p-2">
      <label htmlFor="composer" className="sr-only">
        Ask a question
      </label>
      <textarea
        id="composer"
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, MAX))}
        onKeyDown={onKey}
        rows={2}
        placeholder="Ask about a company or KPI, e.g. What's ORBY's QTD total revenue this quarter?"
        className="min-h-[44px] flex-1 resize-none rounded-lg border-0 bg-transparent px-2 py-1 text-sm focus:outline-none"
        disabled={busy}
      />
      <span className="text-xs text-ink-soft">
        {text.length}/{MAX}
      </span>
      {busy ? (
        <Button type="button" variant="ghost" onClick={onStop} aria-label="Stop">
          <Square className="h-4 w-4" /> Stop
        </Button>
      ) : (
        <Button type="submit" disabled={!text.trim()} aria-label="Send">
          <Send className="h-4 w-4" /> Send
        </Button>
      )}
    </form>
  );
}
