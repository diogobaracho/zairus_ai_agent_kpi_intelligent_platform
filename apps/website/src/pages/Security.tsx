import { Section, SectionHeading } from '../components/layout/Section';
import Card from '../components/ui/Card';
import { boundaries, failureModes } from '../data/security';
import { useT } from '../i18n/useT';

export default function Security() {
  const t = useT();
  return (
    <>
      <Section>
        <SectionHeading
          eyebrow={t('security.eyebrow')}
          title={t('security.title')}
          subtitle={t('security.subtitle')}
        />
        <div className="grid gap-6 md:grid-cols-3">
          {boundaries.map((b) => (
            <Card key={b}>
              <h3 className="text-lg font-semibold">{t(`security.boundaries.${b}.title`)}</h3>
              <p className="mt-2 text-sm text-ink-soft">{t(`security.boundaries.${b}.text`)}</p>
            </Card>
          ))}
        </div>
      </Section>
      <Section tone="mist">
        <SectionHeading
          eyebrow={t('security.failures.eyebrow')}
          title={t('security.failures.title')}
        />
        <div className="mx-auto max-w-4xl overflow-hidden rounded-2xl border border-line bg-white shadow-card">
          <table className="w-full text-sm" aria-label={t('security.failures.tableLabel')}>
            <thead className="bg-paper text-left text-xs uppercase tracking-wide text-ink-soft">
              <tr>
                <th className="p-3">{t('security.failures.mode')}</th>
                <th className="p-3">{t('security.failures.guard')}</th>
              </tr>
            </thead>
            <tbody>
              {failureModes.map((f) => (
                <tr key={f} className="border-t border-line align-top">
                  <td className="p-3 font-semibold">{t(`security.failures.${f}.mode`)}</td>
                  <td className="p-3 text-ink-soft">{t(`security.failures.${f}.guard`)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </>
  );
}
