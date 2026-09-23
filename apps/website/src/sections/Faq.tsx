import { Section, SectionHeading } from '../components/layout/Section';
import Accordion from '../components/ui/Accordion';
import { faq } from '../data/faq';

export default function Faq() {
  return (
    <Section id="faq" tone="white">
      <SectionHeading eyebrow="FAQ" title="Questions investors and engineers ask" />
      <div className="mx-auto max-w-3xl">
        <Accordion items={faq} />
      </div>
    </Section>
  );
}
