import Button from '../components/ui/Button';
import { finalCta } from '../data/home';
import { site } from '../data/site';

export default function FinalCta() {
  return (
    <section className="bg-gradient-to-br from-brand via-brand-dark to-ink py-20 text-white">
      <div className="container-site flex flex-col items-center text-center">
        <h2 className="text-3xl font-bold text-white md:text-4xl">{finalCta.title}</h2>
        <p className="mt-4 max-w-2xl text-white/85">{finalCta.description}</p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Button to={site.chatUrl} variant="light" size="lg">
            {finalCta.primary}
          </Button>
          <Button to="/developers" variant="secondary" size="lg" className="border border-white/30">
            {finalCta.secondary}
          </Button>
        </div>
      </div>
    </section>
  );
}
