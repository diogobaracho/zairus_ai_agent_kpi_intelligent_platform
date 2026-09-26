import { Link } from 'react-router-dom';
import { Mail } from 'lucide-react';
import Logo from './Logo';
import Button from '../ui/Button';
import { footerColumns, site } from '../../data/site';
import { hasChat } from '../../brand';
import LanguageSwitcher from '../../i18n/LanguageSwitcher';
import { useT } from '../../i18n/useT';

export default function Footer() {
  const t = useT();
  return (
    <footer className="bg-ink text-white">
      <div className="container-site grid gap-10 py-14 md:grid-cols-2 lg:grid-cols-5">
        <div className="space-y-4">
          <Logo light />
          <p className="text-sm text-white/70">{t('meta.tagline')}</p>
          <p className="flex items-center gap-2 text-sm text-white/80">
            <Mail className="h-4 w-4 text-brand" /> {site.contact.email}
          </p>
          <LanguageSwitcher dark />
        </div>
        {footerColumns.map((col) => (
          <div key={col.title}>
            <h4 className="mb-4 font-display text-sm font-semibold uppercase tracking-wide text-brand">
              {t(col.title)}
            </h4>
            <ul className="space-y-2 text-sm text-white/80">
              {col.links.map((l) => (
                <li key={l.label}>
                  {l.to.startsWith('http') ? (
                    <a href={l.to} className="hover:text-white" target="_blank" rel="noreferrer">
                      {t(l.label)}
                    </a>
                  ) : (
                    <Link to={l.to} className="hover:text-white">
                      {t(l.label)}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
        {hasChat && (
          <div className="rounded-2xl bg-white/5 p-6">
            <h4 className="font-display text-lg font-semibold">{t('footer.tryTitle')}</h4>
            <p className="mt-2 text-sm text-white/70">{t('footer.tryText')}</p>
            <Button to={site.chatUrl} size="sm" className="mt-4 w-full">
              {t('nav.openChat')}
            </Button>
          </div>
        )}
      </div>
      <div className="border-t border-white/10 py-5 text-center text-xs text-white/60">
        {t('footer.legal', { year: site.year })}
      </div>
    </footer>
  );
}
