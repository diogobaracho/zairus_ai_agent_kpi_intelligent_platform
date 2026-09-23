import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import App from './App';

const routes: [string, RegExp][] = [
  ['/', /Ask your KPI data\. Get answers you can audit\./],
  ['/platform', /One domain layer, three protocol surfaces/],
  ['/developers', /Connect Claude Desktop, Cursor or any MCP client/],
  ['/security', /Boundaries between the model and the data/],
  ['/contact', /Talk to the team/],
];

describe('website', () => {
  it.each(routes)('renders %s', (path, heading) => {
    render(
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByText(heading)).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument();
  });

  it('lists the four MCP tools', () => {
    render(
      <MemoryRouter initialEntries={['/developers']}>
        <App />
      </MemoryRouter>,
    );
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
