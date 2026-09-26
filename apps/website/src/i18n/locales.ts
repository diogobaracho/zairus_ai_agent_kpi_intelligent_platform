import en from './messages/en.json';
import ptBR from './messages/pt-BR.json';

export const LOCALES = ['en', 'pt-BR'] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = 'en';
export const LOCALE_LABELS: Record<Locale, string> = { en: 'EN', 'pt-BR': 'PT-BR' };
export const STORAGE_KEY = 'website.locale';

type Tree = { [key: string]: string | Tree };

/** Nested JSON is easier to edit; react-intl wants flat ids such as `home.hero.title`. */
export function flatten(tree: Tree, prefix = ''): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(tree)) {
    const id = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'string') out[id] = value;
    else Object.assign(out, flatten(value, id));
  }
  return out;
}

export const MESSAGES: Record<Locale, Record<string, string>> = {
  en: flatten(en),
  'pt-BR': flatten(ptBR),
};

export function toLocale(value: string | null | undefined): Locale | null {
  if (!value) return null;
  const lower = value.toLowerCase();
  if (lower.startsWith('pt')) return 'pt-BR';
  if (lower.startsWith('en')) return 'en';
  return null;
}

function readStored(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function storeLocale(locale: Locale): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // private mode or blocked storage: the choice just lasts for this visit
  }
}

/** `?lang=` wins, then the visitor's saved choice, then the browser language, then English. */
export function detectLocale(
  search: string = window.location.search,
  stored: string | null = readStored(),
  languages: readonly string[] = navigator.languages ?? [navigator.language],
): Locale {
  const fromQuery = toLocale(new URLSearchParams(search).get('lang'));
  if (fromQuery) return fromQuery;
  const fromStorage = toLocale(stored);
  if (fromStorage) return fromStorage;
  for (const lang of languages) {
    const match = toLocale(lang);
    if (match) return match;
  }
  return DEFAULT_LOCALE;
}
