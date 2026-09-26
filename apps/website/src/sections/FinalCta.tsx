import Button from '../components/ui/Button';
import { site } from '../data/site';
import { hasChat } from '../brand';
import { useT } from '../i18n/useT';

export default function FinalCta() {
  const t = useT();
  return (
    <section className="bg-gradient-to-br from-brand via-brand-dark to-ink py-20 text-white">
      <div className="container-site flex flex-col items-center text-center">
        <h2 className="text-3xl font-bold text-white md:text-4xl">{t('home.finalCta.title')}</h2>
        <p className="mt-4 max-w-2xl text-white/85">{t('home.finalCta.description')}</p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          {hasChat && (
            <Button to={site.chatUrl} variant="light" size="lg">
              {t('home.finalCta.primary')}
            </Button>
          )}
          <Button to="/developers" variant="secondary" size="lg" className="border border-white/30">
            {t('home.finalCta.secondary')}
          </Button>
        </div>
      </div>
    </section>
  );
}
