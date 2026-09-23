import type { CodeSample } from '../../types/content';

export default function CodeBlock({ title, code }: CodeSample) {
  return (
    <figure className="overflow-hidden rounded-2xl border border-line bg-white shadow-card">
      <figcaption className="border-b border-line px-4 py-2 text-xs font-semibold uppercase tracking-wide text-ink-soft">
        {title}
      </figcaption>
      <pre className="code rounded-none">
        <code>{code}</code>
      </pre>
    </figure>
  );
}
