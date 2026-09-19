import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: '#0B1220', soft: '#334155' },
        paper: '#F7F8FB',
        brand: { DEFAULT: '#2F6BFF', dark: '#1E4FD1', soft: '#E3ECFF' },
        mint: '#22C55E',
        amber: '#F59E0B',
        rose: '#EF4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config;
