import { brand, hasApiDocs, hasChat } from '../brand';
import type { NavItem } from '../types/content';

export const site = {
  brand: brand.brand,
  product: brand.product,
  provider: brand.dataProvider,
  chatUrl: brand.chatUrl,
  apiDocsUrl: brand.apiDocsUrl,
  contact: brand.contact,
  year: new Date().getFullYear(),
};

// `label` is a message id (see src/i18n/messages).
export const nav: NavItem[] = [
  { label: 'nav.product', to: '/' },
  { label: 'nav.platform', to: '/platform' },
  { label: 'nav.developers', to: '/developers' },
  { label: 'nav.security', to: '/security' },
  { label: 'nav.contact', to: '/contact' },
];

export const footerColumns: { title: string; links: NavItem[] }[] = [
  {
    title: 'footer.product',
    links: [
      { label: 'footer.howItWorks', to: '/#how-it-works' },
      { label: 'footer.explainable', to: '/#explainability' },
      { label: 'footer.coverage', to: '/#coverage' },
      { label: 'footer.faq', to: '/#faq' },
    ],
  },
  {
    title: 'footer.platform',
    links: [
      { label: 'footer.architecture', to: '/platform' },
      { label: 'footer.mcpTools', to: '/developers#tools' },
      { label: 'footer.restApi', to: '/developers#rest' },
      { label: 'footer.guardrails', to: '/security' },
    ],
  },
  {
    title: 'footer.getStarted',
    links: [
      ...(hasChat ? [{ label: 'nav.openChat', to: site.chatUrl }] : []),
      ...(hasApiDocs ? [{ label: 'nav.apiDocs', to: site.apiDocsUrl }] : []),
      { label: 'footer.connectClaude', to: '/developers#connect' },
      { label: 'nav.contact', to: '/contact' },
    ],
  },
];
