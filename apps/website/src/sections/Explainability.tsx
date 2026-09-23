import { Section, SectionHeading } from '../components/layout/Section';
import TraceTimelineMockup from '../components/art/TraceTimelineMockup';

export default function Explainability() {
  return (
    <Section id="explainability" tone="white">
      <SectionHeading
        eyebrow="Explainability"
        title="Every answer carries its evidence"
        subtitle="Which tools ran, with which arguments, what came back, and how long it took. One trace id joins the chat, the API logs, the MCP logs and the audit table."
      />
      <div className="mx-auto max-w-4xl">
        <TraceTimelineMockup />
      </div>
      <p className="mx-auto mt-6 max-w-2xl text-center text-sm text-ink-soft">
        Failures are surfaced, not hidden: a wrong ticker shows up as an error step with the
        suggestion the assistant used to recover.
      </p>
    </Section>
  );
}
