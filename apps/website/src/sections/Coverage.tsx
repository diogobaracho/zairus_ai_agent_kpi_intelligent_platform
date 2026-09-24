import { Section, SectionHeading } from '../components/layout/Section';
import MetricStat from '../components/ui/MetricStat';
import { metrics } from '../data/home';
import { brand } from '../brand';

export default function Coverage() {
  return (
    <Section id="coverage" tone="ink">
      <SectionHeading
        dark
        eyebrow="Coverage"
        title="What the sample dataset holds"
        subtitle={`Illustrative ${brand.dataProvider} estimates: enough to explore trends, compare quarters and test every failure mode.`}
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <MetricStat key={m.label} {...m} dark />
        ))}
      </div>
    </Section>
  );
}
