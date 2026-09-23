import type { ReactNode } from 'react';

const tones = {
  brand: 'bg-brand-soft text-brand-dark',
  mint: 'bg-green-50 text-green-700',
  ink: 'bg-ink text-white',
  mist: 'bg-mist text-ink-soft',
  amber: 'bg-amber-50 text-amber-700',
  rose: 'bg-red-50 text-red-700',
};

export default function Badge({
  children,
  tone = 'brand',
}: {
  children: ReactNode;
  tone?: keyof typeof tones;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${tones[tone]}`}
    >
      {children}
    </span>
  );
}
