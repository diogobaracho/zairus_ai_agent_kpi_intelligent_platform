import { Section, SectionHeading } from '../components/layout/Section';
import Accordion from '../components/ui/Accordion';
import { faqIds } from '../data/faq';
import { useT } from '../i18n/useT';

export default function Faq() {
  const t = useT();
  const items = faqIds.map((id) => ({ question: t(`faq.${id}.q`), answer: t(`faq.${id}.a`) }));
  return (
    <Section id="faq" tone="white">
      <SectionHeading eyebrow={t('home.faq.eyebrow')} title={t('home.faq.title')} />
      <div className="mx-auto max-w-3xl">
        <Accordion items={items} />
      </div>
    </Section>
  );
}
