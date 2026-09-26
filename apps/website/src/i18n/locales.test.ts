import { describe, expect, it } from 'vitest';
import en from './messages/en.json';
import ptBR from './messages/pt-BR.json';
import { MESSAGES, detectLocale, flatten, toLocale } from './locales';

describe('message catalogs', () => {
  it('have exactly the same keys in every language', () => {
    const enKeys = Object.keys(flatten(en)).sort();
    const ptKeys = Object.keys(flatten(ptBR)).sort();
    expect(ptKeys.filter((k) => !enKeys.includes(k))).toEqual([]);
    expect(enKeys.filter((k) => !ptKeys.includes(k))).toEqual([]);
  });

  it('keep the same placeholders across languages', () => {
    const placeholders = (s: string) => [...s.matchAll(/\{(\w+)/g)].map((m) => m[1]).sort();
    for (const [id, text] of Object.entries(MESSAGES.en)) {
      expect(placeholders(MESSAGES['pt-BR'][id]), id).toEqual(placeholders(text));
    }
  });

  it('have no empty strings', () => {
    for (const catalog of Object.values(MESSAGES)) {
      expect(Object.entries(catalog).filter(([, v]) => !v.trim())).toEqual([]);
    }
  });
});

describe('detectLocale', () => {
  it('defaults to English', () => {
    expect(detectLocale('', null, ['de-DE', 'fr'])).toBe('en');
    expect(detectLocale('', null, [])).toBe('en');
  });

  it('prefers ?lang=, then the saved choice, then the browser', () => {
    expect(detectLocale('?lang=pt-BR', 'en', ['en-US'])).toBe('pt-BR');
    expect(detectLocale('?lang=xx', 'pt-BR', ['en-US'])).toBe('pt-BR');
    expect(detectLocale('', null, ['fr-FR', 'pt-PT'])).toBe('pt-BR');
  });

  it('maps language tags loosely', () => {
    expect(toLocale('PT')).toBe('pt-BR');
    expect(toLocale('en-GB')).toBe('en');
    expect(toLocale('es')).toBeNull();
  });
});
