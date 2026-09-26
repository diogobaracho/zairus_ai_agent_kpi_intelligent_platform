import { Section, SectionHeading } from '../components/layout/Section';
import ArchitectureArt from '../components/art/ArchitectureArt';
import Card from '../components/ui/Card';
import MetricStat from '../components/ui/MetricStat';
import { layerItems, layers, observability, tenancy } from '../data/platform';
import { useT } from '../i18n/useT';

export default function Platform() {
  const t = useT();
  return (
    <>
      <Section>
        <SectionHeading
          eyebrow={t('platform.eyebrow')}
          title={t('platform.title')}
          subtitle={t('platform.subtitle')}
        />
        <div className="rounded-3xl border border-line bg-white p-4 shadow-card md:p-8">
          <ArchitectureArt />
        </div>
        <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {layers.map((l) => (
            <Card key={l}>
              <h3 className="text-lg font-semibold">{t(`platform.layers.${l}.name`)}</h3>
              <ul className="mt-3 space-y-2 text-sm text-ink-soft">
                {layerItems.map((i) => (
                  <li key={i}>• {t(`platform.layers.${l}.${i}`)}</li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      </Section>
      <Section tone="mist" id="tenancy">
        <SectionHeading
          eyebrow={t('platform.tenancy.eyebrow')}
          title={t('platform.tenancy.title')}
        />
        <ul className="mx-auto max-w-3xl space-y-3 text-ink-soft">
          {tenancy.map((i) => (
            <li key={i} className="rounded-2xl bg-white p-4 shadow-card">
              {t(`platform.tenancy.${i}`)}
            </li>
          ))}
        </ul>
      </Section>
      <Section tone="ink" id="observability">
        <SectionHeading
          dark
          eyebrow={t('platform.observability.eyebrow')}
          title={t('platform.observability.title')}
          subtitle={t('platform.observability.subtitle')}
        />
        <div className="grid gap-4 sm:grid-cols-3">
          {observability.map((m) => (
            <MetricStat
              key={m.id}
              value={m.value}
              label={t(`platform.observability.${m.id}.label`)}
              detail={t(`platform.observability.${m.id}.detail`)}
              dark
            />
          ))}
        </div>
      </Section>
    </>
  );
}
