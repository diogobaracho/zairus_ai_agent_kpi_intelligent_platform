import { Check } from 'lucide-react';
import { Section, SectionHeading } from '../components/layout/Section';
import Card from '../components/ui/Card';
import { capabilities, capabilityBullets } from '../data/home';
import { useT } from '../i18n/useT';

export default function Capabilities() {
  const t = useT();
  return (
    <Section id="capabilities">
      <SectionHeading
        eyebrow={t('home.capabilities.eyebrow')}
        title={t('home.capabilities.title')}
        subtitle={t('home.capabilities.subtitle')}
      />
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {capabilities.map((c) => (
          <Card key={c.id}>
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-soft text-brand">
              <c.icon className="h-5 w-5" />
            </span>
            <h3 className="mt-4 text-lg font-semibold">{t(`home.capabilities.${c.id}.title`)}</h3>
            <ul className="mt-3 space-y-2 text-sm text-ink-soft">
              {capabilityBullets.map((b) => (
                <li key={b} className="flex gap-2">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-mint" />
                  {t(`home.capabilities.${c.id}.${b}`)}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </Section>
  );
}
