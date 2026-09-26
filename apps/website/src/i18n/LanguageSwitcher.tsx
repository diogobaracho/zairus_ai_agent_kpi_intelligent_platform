import { useIntl } from 'react-intl';
import { useLocale } from './context';
import { LOCALES, LOCALE_LABELS } from './locales';

export default function LanguageSwitcher({ dark = false }: { dark?: boolean }) {
  const { locale, setLocale } = useLocale();
  const intl = useIntl();
  const idle = dark ? 'text-white/70 hover:text-white' : 'text-ink-soft hover:text-brand';
  return (
    <div
      role="group"
      aria-label={intl.formatMessage({ id: 'meta.language' })}
      className="inline-flex items-center gap-1 text-xs font-semibold"
    >
      {LOCALES.map((l) => (
        <button
          key={l}
          type="button"
          lang={l}
          aria-pressed={l === locale}
          onClick={() => setLocale(l)}
          className={`rounded-md px-2 py-1 transition-colors ${
            l === locale ? 'bg-brand text-white' : idle
          }`}
        >
          {LOCALE_LABELS[l]}
        </button>
      ))}
    </div>
  );
}
