import { Section, SectionHeading } from '../components/layout/Section';
import Card from '../components/ui/Card';
import { guardrails } from '../data/home';
import { useT } from '../i18n/useT';

export default function Guardrails() {
  const t = useT();
  return (
    <Section id="guardrails">
      <SectionHeading
        eyebrow={t('home.guardrails.eyebrow')}
        title={t('home.guardrails.title')}
        subtitle={t('home.guardrails.subtitle')}
      />
      <div className="grid gap-6 md:grid-cols-2">
        {guardrails.map((g) => (
          <Card key={g.id} className="flex gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-soft text-brand">
              <g.icon className="h-5 w-5" />
            </span>
            <div>
              <h3 className="text-lg font-semibold">{t(`home.guardrails.${g.id}.title`)}</h3>
              <p className="mt-2 text-sm text-ink-soft">
                {t(`home.guardrails.${g.id}.description`)}
              </p>
            </div>
          </Card>
        ))}
      </div>
    </Section>
  );
}
