import { Check } from 'lucide-react';
import Button from '../components/ui/Button';
import AgentChatMockup from '../components/art/AgentChatMockup';
import { hero } from '../data/home';
import { site } from '../data/site';

export default function Hero() {
  return (
    <section className="grain">
      <div className="container-site grid items-center gap-10 py-16 md:py-24 lg:grid-cols-2">
        <div className="animate-rise">
          <span className="eyebrow mb-5">{hero.eyebrow}</span>
          <h1 className="text-4xl font-bold leading-tight md:text-5xl lg:text-[56px] lg:leading-[1.1]">
            {hero.title}
          </h1>
          <p className="mt-6 max-w-xl text-lg text-ink-soft">{hero.description}</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button to={site.chatUrl} size="lg">
              {hero.primaryCta}
            </Button>
            <Button to="/developers#connect" variant="ghost" size="lg">
              {hero.secondaryCta}
            </Button>
          </div>
          <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-soft">
            {hero.badges.map((b) => (
              <li key={b} className="flex items-center gap-2">
                <Check className="h-4 w-4 text-mint" /> {b}
              </li>
            ))}
          </ul>
        </div>
        <AgentChatMockup />
      </div>
    </section>
  );
}
