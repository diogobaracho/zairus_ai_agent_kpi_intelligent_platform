import { Check } from 'lucide-react';
import { Section, SectionHeading } from '../components/layout/Section';
import Card from '../components/ui/Card';
import { capabilities } from '../data/home';

export default function Capabilities() {
  return (
    <Section id="capabilities">
      <SectionHeading
        eyebrow="Capabilities"
        title="Three surfaces, one source of truth"
        subtitle="A REST API for products, an MCP server for AI agents and an explainable chat for people, all over the same governed data layer."
      />
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {capabilities.map((c) => (
          <Card key={c.title}>
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-soft text-brand">
              <c.icon className="h-5 w-5" />
            </span>
            <h3 className="mt-4 text-lg font-semibold">{c.title}</h3>
            <ul className="mt-3 space-y-2 text-sm text-ink-soft">
              {c.bullets.map((b) => (
                <li key={b} className="flex gap-2">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-mint" />
                  {b}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </Section>
  );
}
