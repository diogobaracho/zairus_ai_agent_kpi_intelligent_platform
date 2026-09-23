import type { HTMLAttributes } from 'react';

export default function Card({
  className = '',
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-2xl border border-line bg-white p-6 shadow-card ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}
