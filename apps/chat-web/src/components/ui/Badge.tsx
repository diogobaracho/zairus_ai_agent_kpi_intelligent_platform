import type { ReactNode } from 'react';

const tones = {
  ok: 'bg-green-50 text-green-700 border-green-200',
  warn: 'bg-amber-50 text-amber-700 border-amber-200',
  bad: 'bg-red-50 text-red-700 border-red-200',
  muted: 'bg-slate-50 text-slate-600 border-slate-200',
  brand: 'bg-brand-soft text-brand-dark border-blue-200',
};

export function Badge({
  tone = 'muted',
  children,
}: {
  tone?: keyof typeof tones;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}
