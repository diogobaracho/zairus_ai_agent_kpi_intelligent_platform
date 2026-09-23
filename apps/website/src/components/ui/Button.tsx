import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Link } from 'react-router-dom';

type Variant = 'primary' | 'secondary' | 'ghost' | 'light';
type Size = 'sm' | 'md' | 'lg';

const base =
  'inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-60';
const variants: Record<Variant, string> = {
  primary: 'bg-brand text-white hover:bg-brand-dark shadow-card',
  secondary: 'bg-ink text-white hover:bg-ink-soft',
  ghost: 'bg-transparent text-ink hover:bg-mist border border-line',
  light: 'bg-white text-ink hover:bg-mist',
};
const sizes: Record<Size, string> = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-5 py-3 text-sm md:text-base',
  lg: 'px-7 py-4 text-base',
};

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  to?: string;
  children: ReactNode;
}

export default function Button({
  variant = 'primary',
  size = 'md',
  to,
  className = '',
  children,
  ...rest
}: Props) {
  const cls = `${base} ${variants[variant]} ${sizes[size]} ${className}`;
  if (to) {
    return to.startsWith('http') ? (
      <a href={to} className={cls} target="_blank" rel="noreferrer">
        {children}
      </a>
    ) : (
      <Link to={to} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button className={cls} {...rest}>
      {children}
    </button>
  );
}
