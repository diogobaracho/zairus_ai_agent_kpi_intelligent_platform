import { brand } from '../../brand';

export default function Logo({ light = false }: { light?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2">
      <svg viewBox="0 0 32 32" className="h-9 w-9" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="#2F6BFF" />
        <path
          d="M8 22 L14 12 L19 18 L24 9"
          stroke="#fff"
          strokeWidth="3"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className={`font-display text-xl font-bold ${light ? 'text-white' : 'text-ink'}`}>
        {brand.brand}
        <span className="text-brand"> KPI</span>
      </span>
    </span>
  );
}
