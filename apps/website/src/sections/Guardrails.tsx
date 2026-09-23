import { Section, SectionHeading } from '../components/layout/Section';
import Card from '../components/ui/Card';
import { guardrails } from '../data/home';

export default function Guardrails() {
  return (
    <Section id="guardrails">
      <SectionHeading
        eyebrow="Guardrails"
        title="Designed around how LLM tool calling fails"
        subtitle="Hallucinated identifiers, loops, oversized results and refusals each have a named guard and a test."
      />
      <div className="grid gap-6 md:grid-cols-2">
        {guardrails.map((g) => (
          <Card key={g.title} className="flex gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-soft text-brand">
              <g.icon className="h-5 w-5" />
            </span>
            <div>
              <h3 className="text-lg font-semibold">{g.title}</h3>
              <p className="mt-2 text-sm text-ink-soft">{g.description}</p>
            </div>
          </Card>
        ))}
      </div>
    </Section>
  );
}
