import { Section, SectionHeading } from '../components/layout/Section';
import Button from '../components/ui/Button';
import { steps } from '../data/home';
import { site } from '../data/site';

export default function HowItWorks() {
  return (
    <Section id="how-it-works" tone="mist">
      <SectionHeading
        eyebrow="How it works"
        title="From a question to an auditable answer"
        subtitle="Built for time-constrained investors: one question, one well-chosen tool call, one cited answer."
      />
      <ol className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {steps.map((s) => (
          <li key={s.number} className="relative rounded-2xl bg-white p-6 shadow-card">
            <span className="font-display text-4xl font-bold text-brand/30">{s.number}</span>
            <h3 className="mt-2 text-xl font-semibold">{s.title}</h3>
            <p className="mt-2 text-sm text-ink-soft">{s.description}</p>
          </li>
        ))}
      </ol>
      <div className="mt-10 flex flex-col justify-center gap-3 sm:flex-row">
        <Button to={site.chatUrl}>Open the chat demo</Button>
        <Button to="/platform" variant="ghost">
          See the architecture
        </Button>
      </div>
    </Section>
  );
}
