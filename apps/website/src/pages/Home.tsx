import Hero from '../sections/Hero';
import TrustBar from '../sections/TrustBar';
import HowItWorks from '../sections/HowItWorks';
import Capabilities from '../sections/Capabilities';
import Explainability from '../sections/Explainability';
import Coverage from '../sections/Coverage';
import ForDevelopers from '../sections/ForDevelopers';
import Guardrails from '../sections/Guardrails';
import Faq from '../sections/Faq';
import FinalCta from '../sections/FinalCta';

export default function Home() {
  return (
    <>
      <Hero />
      <TrustBar />
      <HowItWorks />
      <Capabilities />
      <Explainability />
      <Coverage />
      <ForDevelopers />
      <Guardrails />
      <Faq />
      <FinalCta />
    </>
  );
}
