import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import react from '@vitejs/plugin-react';
import type { Plugin } from 'vite';
import { defineConfig } from 'vitest/config';

// White-label: everything brand-specific comes from one JSON file. Defaults to the repo root
// file; BRAND_CONFIG points a standalone build at any other file.
const brandPath = resolve(__dirname, process.env.BRAND_CONFIG ?? '../../brand.config.json');
if (!existsSync(brandPath)) {
  throw new Error(`Brand config not found at ${brandPath}. Set BRAND_CONFIG to a brand JSON file.`);
}
const brand = JSON.parse(readFileSync(brandPath, 'utf-8'));
const siteUrl = String(process.env.VITE_SITE_URL ?? brand.links?.siteUrl ?? '').replace(/\/$/, '');
const pages = ['/', '/platform', '/developers', '/security', '/contact'];

function brandPlugin(): Plugin {
  return {
    name: 'brand',
    // index.html placeholders such as %BRAND_PRODUCT% or %SITE_URL%; `pre` so they are replaced
    // before Vite parses the URLs in the document.
    transformIndexHtml: {
      order: 'pre',
      handler: (html) =>
        html
          .replaceAll('%BRAND_NAME%', brand.brand)
          .replaceAll('%BRAND_PRODUCT%', brand.product)
          .replaceAll('%BRAND_PROVIDER%', brand.dataProvider)
          .replaceAll('%SITE_URL%', siteUrl),
    },
    generateBundle() {
      this.emitFile({
        type: 'asset',
        fileName: 'robots.txt',
        source: `User-agent: *\nAllow: /\n${siteUrl ? `Sitemap: ${siteUrl}/sitemap.xml\n` : ''}`,
      });
      if (!siteUrl) return;
      const urls = pages.map((p) => `  <url><loc>${siteUrl}${p}</loc></url>`).join('\n');
      this.emitFile({
        type: 'asset',
        fileName: 'sitemap.xml',
        source: `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), brandPlugin()],
  resolve: { alias: { '@brand': brandPath } },
  test: { environment: 'jsdom', globals: true, setupFiles: ['./src/test/setup.ts'], css: false },
});
