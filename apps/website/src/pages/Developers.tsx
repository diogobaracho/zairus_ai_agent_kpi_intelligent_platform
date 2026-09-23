import { Section, SectionHeading } from '../components/layout/Section';
import Button from '../components/ui/Button';
import CodeBlock from '../components/ui/CodeBlock';
import { quickstart, samples, tools } from '../data/developers';
import { site } from '../data/site';

export default function Developers() {
  return (
    <>
      <Section>
        <SectionHeading
          eyebrow="Developers"
          title="Run it, connect it, query it"
          subtitle="Everything starts with one command and works without an LLM API key."
        />
        <div className="mx-auto max-w-3xl">
          <CodeBlock title="Quickstart" language="bash" code={quickstart.join('\n')} />
        </div>
      </Section>
      <Section tone="mist" id="connect">
        <SectionHeading
          eyebrow="MCP"
          title="Connect Claude Desktop, Cursor or any MCP client"
          subtitle="stdio for desktop clients, streamable HTTP for services. Every call lands in the same audit table."
        />
        <div className="grid gap-6 lg:grid-cols-2">
          <CodeBlock {...samples[0]} />
          <CodeBlock {...samples[1]} />
        </div>
      </Section>
      <Section id="tools" tone="white">
        <SectionHeading eyebrow="Tools" title="The four tools" />
        <div className="grid gap-4 md:grid-cols-2">
          {tools.map((t) => (
            <div key={t.name} className="rounded-2xl border border-line bg-paper p-5 text-sm">
              <div className="font-mono font-semibold text-brand-dark">{t.name}</div>
              <p className="mt-2 text-ink-soft">{t.purpose}</p>
              <p className="mt-2">
                <span className="font-semibold">params:</span>{' '}
                <span className="font-mono text-xs">{t.params}</span>
              </p>
              <p className="mt-1">
                <span className="font-semibold">returns:</span>{' '}
                <span className="font-mono text-xs">{t.returns}</span>
              </p>
            </div>
          ))}
        </div>
        <div className="mt-8">
          <CodeBlock {...samples[3]} />
        </div>
      </Section>
      <Section id="rest" tone="mist">
        <SectionHeading
          eyebrow="REST"
          title="The same data over HTTP"
          subtitle="Typed JSON, problem+json errors with suggestions, OpenAPI document, SSE chat endpoint."
        />
        <div className="mx-auto max-w-3xl">
          <CodeBlock {...samples[2]} />
        </div>
        <div className="mt-8 text-center">
          <Button to={site.apiDocsUrl}>Open the API docs</Button>
        </div>
      </Section>
    </>
  );
}
