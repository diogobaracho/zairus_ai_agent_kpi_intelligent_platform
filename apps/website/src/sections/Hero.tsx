import { Check } from 'lucide-react';
import Button from '../components/ui/Button';
import AgentChatMockup from '../components/art/AgentChatMockup';
import { heroBadges } from '../data/home';
import { site } from '../data/site';
import { hasChat } from '../brand';
import { useT } from '../i18n/useT';

export default function Hero() {
  const t = useT();
  return (
    <section className="grain">
      <div className="container-site grid items-center gap-10 py-16 md:py-24 lg:grid-cols-2">
        <div className="animate-rise">
          <span className="eyebrow mb-5">{t('home.hero.eyebrow')}</span>
          <h1 className="text-4xl font-bold leading-tight md:text-5xl lg:text-[56px] lg:leading-[1.1]">
            {t('home.hero.title')}
          </h1>
          <p className="mt-6 max-w-xl text-lg text-ink-soft">{t('home.hero.description')}</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            {hasChat && (
              <Button to={site.chatUrl} size="lg">
                {t('home.hero.primaryCta')}
              </Button>
            )}
            <Button to="/developers#connect" variant="ghost" size="lg">
              {t('home.hero.secondaryCta')}
            </Button>
          </div>
          <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-soft">
            {heroBadges.map((b) => (
              <li key={b} className="flex items-center gap-2">
                <Check className="h-4 w-4 text-mint" /> {t(`home.hero.badges.${b}`)}
              </li>
            ))}
          </ul>
        </div>
        <AgentChatMockup />
      </div>
    </section>
  );
}
