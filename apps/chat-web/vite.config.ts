import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import react from '@vitejs/plugin-react';
import type { Plugin } from 'vite';
import { defineConfig } from 'vitest/config';

// Same white-label file as the website and the Python services (see brand.config.json).
const brandPath = resolve(__dirname, process.env.BRAND_CONFIG ?? '../../brand.config.json');
if (!existsSync(brandPath)) {
  throw new Error(`Brand config not found at ${brandPath}. Set BRAND_CONFIG to a brand JSON file.`);
}
const brand = JSON.parse(readFileSync(brandPath, 'utf-8'));

function brandHtml(): Plugin {
  return {
    name: 'brand-html',
    transformIndexHtml: {
      order: 'pre',
      handler: (html) =>
        html
          .replaceAll('%BRAND_NAME%', brand.brand)
          .replaceAll('%BRAND_PRODUCT%', brand.product)
          .replaceAll('%BRAND_PROVIDER%', brand.dataProvider),
    },
  };
}

export default defineConfig({
  plugins: [react(), brandHtml()],
  resolve: { alias: { '@brand': brandPath } },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: { recharts: ['recharts'], react: ['react', 'react-dom', 'react-router-dom'] },
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
});
