import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';
import App from './App';
import LocaleProvider from './i18n/LocaleProvider';
import type { Locale } from './i18n/locales';

function renderAt(path: string, locale: Locale = 'en') {
  return render(
    <LocaleProvider initialLocale={locale}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </LocaleProvider>,
  );
}

const routes: [string, RegExp, RegExp][] = [
  ['/', /Ask your KPI data\. Get answers you can audit\./, /Pergunte aos seus KPIs/],
  ['/platform', /One domain layer, three protocol surfaces/, /Uma camada de domínio/],
  ['/developers', /Connect Claude Desktop, Cursor or any MCP client/, /Conecte o Claude Desktop/],
  ['/security', /Boundaries between the model and the data/, /Fronteiras entre o modelo/],
  ['/contact', /Talk to the team/, /Fale com o time/],
];

describe('website', () => {
  beforeEach(() => window.localStorage.clear());

  it.each(routes)('renders %s in English', (path, heading) => {
    renderAt(path);
    expect(screen.getByText(heading)).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument();
  });

  it.each(routes)('renders %s in Brazilian Portuguese', (path, _en, heading) => {
    renderAt(path, 'pt-BR');
    expect(screen.getByText(heading)).toBeInTheDocument();
    expect(document.documentElement.lang).toBe('pt-BR');
  });

  it('switches language from the header and remembers the choice', async () => {
    renderAt('/');
    const [ptButton] = screen.getAllByRole('button', { name: 'PT-BR' });
    await userEvent.click(ptButton);
    expect(screen.getByText(/Pergunte aos seus KPIs/)).toBeInTheDocument();
    expect(window.localStorage.getItem('website.locale')).toBe('pt-BR');
    expect(screen.getAllByRole('button', { name: 'PT-BR' })[0]).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  it('takes brand names and contact details from brand.config.json', () => {
    renderAt('/contact');
    expect(screen.getAllByText('hello@zairus.example.com').length).toBeGreaterThan(0);
    expect(screen.getByText('+1 (555) 010-2030')).toBeInTheDocument();
    expect(screen.getByText(/© \d{4} Zairus KPI Intelligent Platform/)).toBeInTheDocument();
  });

  it('lists the four MCP tools', () => {
    renderAt('/developers');
    for (const name of [
      'search_companies',
      'list_company_kpis',
      'get_kpi_history',
      'get_kpi_qtd',
    ]) {
      expect(screen.getAllByText(name).length).toBeGreaterThan(0);
    }
  });
});
