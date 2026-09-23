import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import type { FaqItem } from '../../types/content';

export default function Accordion({ items }: { items: FaqItem[] }) {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div className="divide-y divide-line rounded-2xl border border-line bg-white">
      {items.map((item, i) => {
        const isOpen = open === i;
        return (
          <div key={item.question}>
            <button
              className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left font-semibold text-ink hover:bg-paper"
              onClick={() => setOpen(isOpen ? null : i)}
              aria-expanded={isOpen}
            >
              <span>{item.question}</span>
              <ChevronDown
                className={`h-5 w-5 shrink-0 text-brand transition-transform ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>
            {isOpen && <p className="px-5 pb-5 text-ink-soft">{item.answer}</p>}
          </div>
        );
      })}
    </div>
  );
}
