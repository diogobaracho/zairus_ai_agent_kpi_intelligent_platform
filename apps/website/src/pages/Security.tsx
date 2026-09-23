import { Section, SectionHeading } from '../components/layout/Section';
import Card from '../components/ui/Card';
import { boundaries, failureModes } from '../data/security';

export default function Security() {
  return (
    <>
      <Section>
        <SectionHeading
          eyebrow="Security"
          title="Boundaries between the model and the data"
          subtitle="No login is needed for the demo, so the design focuses on the boundaries that matter for an agent platform."
        />
        <div className="grid gap-6 md:grid-cols-3">
          {boundaries.map((b) => (
            <Card key={b.title}>
              <h3 className="text-lg font-semibold">{b.title}</h3>
              <p className="mt-2 text-sm text-ink-soft">{b.text}</p>
            </Card>
          ))}
        </div>
      </Section>
      <Section tone="mist">
        <SectionHeading eyebrow="Failure modes" title="Each failure mode has a guard and a test" />
        <div className="mx-auto max-w-4xl overflow-hidden rounded-2xl border border-line bg-white shadow-card">
          <table className="w-full text-sm" aria-label="Failure modes and guards">
            <thead className="bg-paper text-left text-xs uppercase tracking-wide text-ink-soft">
              <tr>
                <th className="p-3">failure mode</th>
                <th className="p-3">guard</th>
              </tr>
            </thead>
            <tbody>
              {failureModes.map((f) => (
                <tr key={f.mode} className="border-t border-line align-top">
                  <td className="p-3 font-semibold">{f.mode}</td>
                  <td className="p-3 text-ink-soft">{f.guard}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </>
  );
}
