import { Section, SectionHeading } from '../components/layout/Section';
import ArchitectureArt from '../components/art/ArchitectureArt';
import Card from '../components/ui/Card';
import MetricStat from '../components/ui/MetricStat';
import { layers, observability, tenancy } from '../data/platform';

export default function Platform() {
  return (
    <>
      <Section>
        <SectionHeading
          eyebrow="Platform"
          title="One domain layer, three protocol surfaces"
          subtitle="REST, MCP and the chat agent are thin adapters over the same services, so validation, suggestions and error semantics are defined once."
        />
        <div className="rounded-3xl border border-line bg-white p-4 shadow-card md:p-8">
          <ArchitectureArt />
        </div>
        <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {layers.map((l) => (
            <Card key={l.name}>
              <h3 className="text-lg font-semibold">{l.name}</h3>
              <ul className="mt-3 space-y-2 text-sm text-ink-soft">
                {l.items.map((i) => (
                  <li key={i}>• {i}</li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      </Section>
      <Section tone="mist" id="tenancy">
        <SectionHeading
          eyebrow="Multi-tenant ready"
          title="Identity from the server, never from the model"
        />
        <ul className="mx-auto max-w-3xl space-y-3 text-ink-soft">
          {tenancy.map((t) => (
            <li key={t} className="rounded-2xl bg-white p-4 shadow-card">
              {t}
            </li>
          ))}
        </ul>
      </Section>
      <Section tone="ink" id="observability">
        <SectionHeading
          dark
          eyebrow="Observability"
          title="Traceable end to end"
          subtitle="Structured JSON logs, an audit table for tool calls, health and readiness endpoints, optional OpenTelemetry export."
        />
        <div className="grid gap-4 sm:grid-cols-3">
          {observability.map((m) => (
            <MetricStat key={m.label} {...m} dark />
          ))}
        </div>
      </Section>
    </>
  );
}
