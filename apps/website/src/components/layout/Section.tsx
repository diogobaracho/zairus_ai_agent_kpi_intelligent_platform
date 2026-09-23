import type { ReactNode } from 'react';

const tones = { paper: 'bg-paper', mist: 'bg-mist', white: 'bg-white', ink: 'bg-ink text-white' };

interface Props {
  id?: string;
  tone?: keyof typeof tones;
  className?: string;
  children: ReactNode;
}

export function Section({ id, tone = 'paper', className = '', children }: Props) {
  return (
    <section id={id} className={`py-16 md:py-24 ${tones[tone]} ${className}`}>
      <div className="container-site">{children}</div>
    </section>
  );
}

interface HeadingProps {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  align?: 'left' | 'center';
  dark?: boolean;
}

export function SectionHeading({
  eyebrow,
  title,
  subtitle,
  align = 'center',
  dark = false,
}: HeadingProps) {
  return (
    <div className={`mb-12 max-w-3xl ${align === 'center' ? 'mx-auto text-center' : ''}`}>
      {eyebrow && <span className="eyebrow mb-4">{eyebrow}</span>}
      <h2 className={`text-3xl font-bold md:text-4xl ${dark ? 'text-white' : ''}`}>{title}</h2>
      {subtitle && (
        <p className={`mt-4 text-lg ${dark ? 'text-white/75' : 'text-ink-soft'}`}>{subtitle}</p>
      )}
    </div>
  );
}
