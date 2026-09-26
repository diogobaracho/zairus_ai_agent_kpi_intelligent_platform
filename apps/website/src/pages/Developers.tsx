import { Section, SectionHeading } from '../components/layout/Section';
import Button from '../components/ui/Button';
import CodeBlock from '../components/ui/CodeBlock';
import { quickstart, samples, tools } from '../data/developers';
import { site } from '../data/site';
import { hasApiDocs } from '../brand';
import { useT } from '../i18n/useT';

export default function Developers() {
  const t = useT();
  const [stdio, http, rest, envelope] = samples.map((s) => ({ ...s, title: t(s.title) }));
  return (
    <>
      <Section>
        <SectionHeading
          eyebrow={t('developers.eyebrow')}
          title={t('developers.title')}
          subtitle={t('developers.subtitle')}
        />
        <div className="mx-auto max-w-3xl">
          <CodeBlock
            title={t('developers.quickstart')}
            language="bash"
            code={quickstart.join('\n')}
          />
        </div>
      </Section>
      <Section tone="mist" id="connect">
        <SectionHeading
          eyebrow={t('developers.mcp.eyebrow')}
          title={t('developers.mcp.title')}
          subtitle={t('developers.mcp.subtitle')}
        />
        <div className="grid gap-6 lg:grid-cols-2">
          <CodeBlock {...stdio} />
          <CodeBlock {...http} />
        </div>
      </Section>
      <Section id="tools" tone="white">
        <SectionHeading
          eyebrow={t('developers.tools.eyebrow')}
          title={t('developers.tools.title')}
        />
        <div className="grid gap-4 md:grid-cols-2">
          {tools.map((tool) => (
            <div key={tool.name} className="rounded-2xl border border-line bg-paper p-5 text-sm">
              <div className="font-mono font-semibold text-brand-dark">{tool.name}</div>
              <p className="mt-2 text-ink-soft">{t(`developers.toolPurpose.${tool.name}`)}</p>
              <p className="mt-2">
                <span className="font-semibold">{t('developers.tools.params')}</span>{' '}
                <span className="font-mono text-xs">{tool.params}</span>
              </p>
              <p className="mt-1">
                <span className="font-semibold">{t('developers.tools.returns')}</span>{' '}
                <span className="font-mono text-xs">{tool.returns}</span>
              </p>
            </div>
          ))}
        </div>
        <div className="mt-8">
          <CodeBlock {...envelope} />
        </div>
      </Section>
      <Section id="rest" tone="mist">
        <SectionHeading
          eyebrow={t('developers.rest.eyebrow')}
          title={t('developers.rest.title')}
          subtitle={t('developers.rest.subtitle')}
        />
        <div className="mx-auto max-w-3xl">
          <CodeBlock {...rest} />
        </div>
        {hasApiDocs && (
          <div className="mt-8 text-center">
            <Button to={site.apiDocsUrl}>{t('developers.rest.cta')}</Button>
          </div>
        )}
      </Section>
    </>
  );
}
