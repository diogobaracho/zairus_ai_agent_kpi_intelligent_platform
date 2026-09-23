const items = [
  'Model Context Protocol',
  'FastAPI',
  'Postgres 16',
  'Claude models',
  'Docker Compose',
  'OpenAPI',
];

export default function TrustBar() {
  return (
    <div className="border-y border-line bg-white">
      <div className="container-site flex flex-wrap items-center justify-center gap-x-10 gap-y-3 py-5 text-sm font-semibold text-ink-soft">
        <span className="text-xs uppercase tracking-wide">Built with</span>
        {items.map((i) => (
          <span key={i}>{i}</span>
        ))}
      </div>
    </div>
  );
}
