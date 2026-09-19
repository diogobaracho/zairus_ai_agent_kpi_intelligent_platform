const EXAMPLES = [
  "What's ORBY's QTD total revenue this quarter?",
  'Show ORBY total revenue history',
  'Which KPIs does KSTL publish?',
  'Show MMHM GMV trend over the last quarters',
  'Show ORBYY revenue history',
];

export function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="card p-6 text-sm">
      <h2 className="text-base font-semibold">Ask the KPI assistant</h2>
      <p className="mt-1 text-ink-soft">
        Answers come from ZairusData's KPI estimates through four MCP tools. Every tool call is
        shown on the right, with its arguments and result, so you can verify how the answer was
        produced.
      </p>
      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {EXAMPLES.map((q) => (
          <li key={q}>
            <button
              type="button"
              onClick={() => onPick(q)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-left hover:border-brand hover:bg-brand-soft"
            >
              {q}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
