import { useT } from '../i18n/useT';

const items = [
  'Model Context Protocol',
  'FastAPI',
  'Postgres 16',
  null,
  'Docker Compose',
  'OpenAPI',
];

export default function TrustBar() {
  const t = useT();
  return (
    <div className="border-y border-line bg-white">
      <div className="container-site flex flex-wrap items-center justify-center gap-x-10 gap-y-3 py-5 text-sm font-semibold text-ink-soft">
        <span className="text-xs uppercase tracking-wide">{t('home.trustBar.builtWith')}</span>
        {items.map((i) => {
          const label = i ?? t('home.trustBar.claude');
          return <span key={label}>{label}</span>;
        })}
      </div>
    </div>
  );
}
