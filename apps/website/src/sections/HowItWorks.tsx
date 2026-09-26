import { Section, SectionHeading } from '../components/layout/Section';
import Button from '../components/ui/Button';
import { steps } from '../data/home';
import { site } from '../data/site';
import { hasChat } from '../brand';
import { useT } from '../i18n/useT';

export default function HowItWorks() {
  const t = useT();
  return (
    <Section id="how-it-works" tone="mist">
      <SectionHeading
        eyebrow={t('home.howItWorks.eyebrow')}
        title={t('home.howItWorks.title')}
        subtitle={t('home.howItWorks.subtitle')}
      />
      <ol className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {steps.map((s) => (
          <li key={s.id} className="relative rounded-2xl bg-white p-6 shadow-card">
            <span className="font-display text-4xl font-bold text-brand/30">{s.number}</span>
            <h3 className="mt-2 text-xl font-semibold">{t(`home.steps.${s.id}.title`)}</h3>
            <p className="mt-2 text-sm text-ink-soft">{t(`home.steps.${s.id}.description`)}</p>
          </li>
        ))}
      </ol>
      <div className="mt-10 flex flex-col justify-center gap-3 sm:flex-row">
        {hasChat && <Button to={site.chatUrl}>{t('home.hero.primaryCta')}</Button>}
        <Button to="/platform" variant="ghost">
          {t('home.howItWorks.architecture')}
        </Button>
      </div>
    </Section>
  );
}
