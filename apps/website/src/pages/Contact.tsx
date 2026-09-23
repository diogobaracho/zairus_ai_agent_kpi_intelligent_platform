import { useState, type FormEvent } from 'react';
import { Section, SectionHeading } from '../components/layout/Section';
import Button from '../components/ui/Button';
import { site } from '../data/site';

export default function Contact() {
  const [sent, setSent] = useState(false);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    setSent(true);
  };
  return (
    <Section>
      <SectionHeading
        eyebrow="Contact"
        title="Talk to the team"
        subtitle="Interested in connecting your own KPI data, a private deployment or the multi-tenant roadmap?"
      />
      <div className="mx-auto max-w-xl rounded-2xl border border-line bg-white p-6 shadow-card">
        {sent ? (
          <p role="status" className="text-ink">
            Thanks. This demo form does not send anything; write to{' '}
            <a className="text-brand" href={`mailto:${site.contact.email}`}>
              {site.contact.email}
            </a>
            .
          </p>
        ) : (
          <form onSubmit={submit} className="grid gap-4">
            <label className="grid gap-1 text-sm">
              Name
              <input required className="rounded-lg border border-line px-3 py-2" name="name" />
            </label>
            <label className="grid gap-1 text-sm">
              Work email
              <input
                required
                type="email"
                className="rounded-lg border border-line px-3 py-2"
                name="email"
              />
            </label>
            <label className="grid gap-1 text-sm">
              What would you like to do?
              <textarea
                rows={4}
                className="rounded-lg border border-line px-3 py-2"
                name="message"
              />
            </label>
            <Button type="submit">Send</Button>
          </form>
        )}
      </div>
    </Section>
  );
}
