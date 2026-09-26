import { useState, type FormEvent } from 'react';
import { FormattedMessage } from 'react-intl';
import { Section, SectionHeading } from '../components/layout/Section';
import Button from '../components/ui/Button';
import { site } from '../data/site';
import { formatAddress } from '../brand';
import { useT } from '../i18n/useT';

export default function Contact() {
  const t = useT();
  const [sent, setSent] = useState(false);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    setSent(true);
  };
  const email = (
    <a className="text-brand" href={`mailto:${site.contact.email}`}>
      {site.contact.email}
    </a>
  );
  return (
    <Section>
      <SectionHeading
        eyebrow={t('contact.eyebrow')}
        title={t('contact.title')}
        subtitle={t('contact.subtitle')}
      />
      <address className="mx-auto mb-6 grid max-w-xl gap-1 text-center text-sm not-italic text-ink-soft">
        <a className="font-medium text-brand" href={`mailto:${site.contact.email}`}>
          {site.contact.email}
        </a>
        {site.contact.phone && (
          <a href={`tel:${site.contact.phone.replace(/[^+\d]/g, '')}`}>{site.contact.phone}</a>
        )}
        {formatAddress(site.contact.address).map((line) => (
          <span key={line}>{line}</span>
        ))}
      </address>
      <div className="mx-auto max-w-xl rounded-2xl border border-line bg-white p-6 shadow-card">
        {sent ? (
          <p role="status" className="text-ink">
            <FormattedMessage id="contact.sent" values={{ email }} />
          </p>
        ) : (
          <form onSubmit={submit} className="grid gap-4">
            <label className="grid gap-1 text-sm">
              {t('contact.name')}
              <input required className="rounded-lg border border-line px-3 py-2" name="name" />
            </label>
            <label className="grid gap-1 text-sm">
              {t('contact.email')}
              <input
                required
                type="email"
                className="rounded-lg border border-line px-3 py-2"
                name="email"
              />
            </label>
            <label className="grid gap-1 text-sm">
              {t('contact.message')}
              <textarea
                rows={4}
                className="rounded-lg border border-line px-3 py-2"
                name="message"
              />
            </label>
            <Button type="submit">{t('contact.send')}</Button>
          </form>
        )}
      </div>
    </Section>
  );
}
