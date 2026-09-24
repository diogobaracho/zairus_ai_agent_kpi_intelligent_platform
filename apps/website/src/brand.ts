import raw from '@brand';

export interface Address {
  street?: string;
  city?: string;
  region?: string;
  postalCode?: string;
  country?: string;
}

export interface BrandConfig {
  brand: string;
  product: string;
  dataProvider: string;
  assistantName?: string;
  mcpServerName: string;
  contact: { email: string; phone?: string; address?: Address };
  social?: { github?: string; linkedin?: string };
  links?: { siteUrl?: string; chatUrl?: string; apiDocsUrl?: string };
}

const config = raw as BrandConfig;
const env = import.meta.env;

/** Build-time env vars win over the JSON so one image can be pointed at different hosts. */
function pick(envValue: string | undefined, fallback: string | undefined): string {
  return (envValue ?? fallback ?? '').trim();
}

export const brand = {
  ...config,
  chatUrl: pick(env.VITE_CHAT_URL, config.links?.chatUrl),
  apiDocsUrl: pick(env.VITE_API_DOCS_URL, config.links?.apiDocsUrl),
  githubUrl: config.social?.github ?? '',
};

/** The website ships on its own: without a chat deployment the chat CTAs are simply hidden. */
export const hasChat = brand.chatUrl !== '';
export const hasApiDocs = brand.apiDocsUrl !== '';

export function formatAddress(address: Address | undefined): string[] {
  if (!address) return [];
  const cityLine = [address.city, address.region, address.postalCode].filter(Boolean).join(', ');
  return [address.street, cityLine, address.country].filter((l): l is string => Boolean(l));
}
