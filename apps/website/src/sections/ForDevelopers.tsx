import { Section, SectionHeading } from '../components/layout/Section';
import Button from '../components/ui/Button';
import CodeBlock from '../components/ui/CodeBlock';
import { samples, tools } from '../data/developers';
import { useT } from '../i18n/useT';

export default function ForDevelopers() {
  const t = useT();
  const envelope = samples[3];
  return (
    <Section id="developers" tone="mist">
      <SectionHeading
        eyebrow={t('home.developers.eyebrow')}
        title={t('home.developers.title')}
        subtitle={t('home.developers.subtitle')}
      />
      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-card">
          <table className="w-full text-sm" aria-label="MCP tools">
            <thead className="bg-paper text-left text-xs uppercase tracking-wide text-ink-soft">
              <tr>
                <th className="p-3">{t('home.developers.tool')}</th>
                <th className="p-3">{t('home.developers.whenToUse')}</th>
              </tr>
            </thead>
            <tbody>
              {tools.map((tool) => (
                <tr key={tool.name} className="border-t border-line align-top">
                  <td className="p-3 font-mono text-xs font-semibold text-brand-dark">
                    {tool.name}
                    <div className="mt-1 font-normal text-ink-soft">{tool.params}</div>
                  </td>
                  <td className="p-3 text-ink-soft">{t(`developers.toolPurpose.${tool.name}`)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock {...envelope} title={t(envelope.title)} />
      </div>
      <div className="mt-8 text-center">
        <Button to="/developers">{t('home.developers.cta')}</Button>
      </div>
    </Section>
  );
}
