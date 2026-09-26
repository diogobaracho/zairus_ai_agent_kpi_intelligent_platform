import { Section, SectionHeading } from '../components/layout/Section';
import MetricStat from '../components/ui/MetricStat';
import { metrics } from '../data/home';
import { useT } from '../i18n/useT';

export default function Coverage() {
  const t = useT();
  return (
    <Section id="coverage" tone="ink">
      <SectionHeading
        dark
        eyebrow={t('home.coverage.eyebrow')}
        title={t('home.coverage.title')}
        subtitle={t('home.coverage.subtitle')}
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <MetricStat
            key={m.id}
            value={m.value}
            label={t(`home.coverage.${m.id}.label`)}
            detail={t(`home.coverage.${m.id}.detail`, m.values)}
            dark
          />
        ))}
      </div>
    </Section>
  );
}
