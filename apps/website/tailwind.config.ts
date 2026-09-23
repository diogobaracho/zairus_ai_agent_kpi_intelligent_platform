import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: '#0B1220', soft: '#475569' },
        paper: '#F7F8FB',
        mist: '#EEF2F9',
        line: '#DCE3EE',
        brand: { DEFAULT: '#2F6BFF', dark: '#1E4FD1', soft: '#E3ECFF' },
        mint: '#22C55E',
        amber: '#F59E0B',
        rose: '#EF4444',
      },
      fontFamily: {
        display: ['Sora', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        card: '0 10px 30px -12px rgba(11,18,32,0.18)',
        float: '0 18px 50px -20px rgba(11,18,32,0.35)',
      },
      maxWidth: { site: '1200px' },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: { rise: 'rise .6s ease-out both' },
    },
  },
  plugins: [],
} satisfies Config;
