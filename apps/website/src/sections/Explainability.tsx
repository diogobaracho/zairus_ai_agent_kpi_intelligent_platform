import { Section, SectionHeading } from '../components/layout/Section';
import TraceTimelineMockup from '../components/art/TraceTimelineMockup';
import { useT } from '../i18n/useT';

export default function Explainability() {
  const t = useT();
  return (
    <Section id="explainability" tone="white">
      <SectionHeading
        eyebrow={t('home.explainability.eyebrow')}
        title={t('home.explainability.title')}
        subtitle={t('home.explainability.subtitle')}
      />
      <div className="mx-auto max-w-4xl">
        <TraceTimelineMockup />
      </div>
      <p className="mx-auto mt-6 max-w-2xl text-center text-sm text-ink-soft">
        {t('home.explainability.footnote')}
      </p>
    </Section>
  );
}
