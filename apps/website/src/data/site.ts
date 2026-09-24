import { brand, hasApiDocs, hasChat } from '../brand';
import type { NavItem } from '../types/content';

export const site = {
  brand: brand.brand,
  product: brand.product,
  provider: brand.dataProvider,
  tagline: 'KPI estimates for public investors and the AI agents that work for them.',
  chatUrl: brand.chatUrl,
  apiDocsUrl: brand.apiDocsUrl,
  repoDocsUrl: '/developers',
  contact: brand.contact,
  year: new Date().getFullYear(),
};

export const nav: NavItem[] = [
  { label: 'Product', to: '/' },
  { label: 'Platform', to: '/platform' },
  { label: 'Developers', to: '/developers' },
  { label: 'Security', to: '/security' },
  { label: 'Contact', to: '/contact' },
];

export const footerColumns: { title: string; links: NavItem[] }[] = [
  {
    title: 'Product',
    links: [
      { label: 'How it works', to: '/#how-it-works' },
      { label: 'Explainable answers', to: '/#explainability' },
      { label: 'Coverage', to: '/#coverage' },
      { label: 'FAQ', to: '/#faq' },
    ],
  },
  {
    title: 'Platform',
    links: [
      { label: 'Architecture', to: '/platform' },
      { label: 'MCP tools', to: '/developers#tools' },
      { label: 'REST API', to: '/developers#rest' },
      { label: 'Guardrails', to: '/security' },
    ],
  },
  {
    title: 'Get started',
    links: [
      ...(hasChat ? [{ label: 'Open the chat', to: site.chatUrl }] : []),
      ...(hasApiDocs ? [{ label: 'API docs', to: site.apiDocsUrl }] : []),
      { label: 'Connect Claude Desktop', to: '/developers#connect' },
      { label: 'Contact', to: '/contact' },
    ],
  },
];
