import { Section, SectionHeading } from '../components/layout/Section';
import Button from '../components/ui/Button';
import CodeBlock from '../components/ui/CodeBlock';
import { samples, tools } from '../data/developers';

export default function ForDevelopers() {
  return (
    <Section id="developers" tone="mist">
      <SectionHeading
        eyebrow="For developers"
        title="Four tools an agent understands on first read"
        subtitle="Self-describing names, scalar parameters, public identifiers only, structured JSON in and out."
      />
      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-card">
          <table className="w-full text-sm" aria-label="MCP tools">
            <thead className="bg-paper text-left text-xs uppercase tracking-wide text-ink-soft">
              <tr>
                <th className="p-3">tool</th>
                <th className="p-3">when to use</th>
              </tr>
            </thead>
            <tbody>
              {tools.map((t) => (
                <tr key={t.name} className="border-t border-line align-top">
                  <td className="p-3 font-mono text-xs font-semibold text-brand-dark">
                    {t.name}
                    <div className="mt-1 font-normal text-ink-soft">{t.params}</div>
                  </td>
                  <td className="p-3 text-ink-soft">{t.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock {...samples[3]} />
      </div>
      <div className="mt-8 text-center">
        <Button to="/developers">Connect Claude Desktop, Cursor or REST</Button>
      </div>
    </Section>
  );
}
