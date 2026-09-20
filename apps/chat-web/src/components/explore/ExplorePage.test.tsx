import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import ExplorePage from './ExplorePage';

const json = (body: unknown, status = 200) =>
  Promise.resolve(
    new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } }),
  );

describe('ExplorePage', () => {
  afterEach(() => vi.restoreAllMocks());

  it('lists sectors and companies from the API', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input);
      if (url.includes('/v1/sectors'))
        return json({
          items: [
            { name: 'Software', company_count: 1 },
            { name: 'Software', company_count: 3 },
          ],
        });
      return json({
        items: [{ ticker: 'ORBY', name: 'Orbitly Analytics', sector: 'Software' }],
        total: 1,
        suggestions: [],
      });
    });
    render(
      <MemoryRouter>
        <ExplorePage />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getByText('Orbitly Analytics')).toBeInTheDocument(),
    );
    expect(screen.getByRole('option', { name: /Software \(3\)/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /ORBY/ })).toHaveAttribute('href', '/explore/ORBY');
  });

  it('shows suggestions when nothing matches and a problem banner on errors', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input);
      if (url.includes('/v1/sectors')) return json({ items: [] });
      if (url.includes('sector='))
        return json(
          {
            title: 'Sector not found',
            status: 404,
            detail: "No sector named 'Sofware'",
            code: 'sector_not_found',
          },
          404,
        );
      return json({
        items: [],
        total: 0,
        suggestions: [{ value: 'ORBY', label: 'Orbitly Analytics (ORBY)' }],
      });
    });
    render(
      <MemoryRouter>
        <ExplorePage />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText(/No company matched/)).toBeInTheDocument());
    expect(screen.getByRole('link', { name: 'ORBY' })).toBeInTheDocument();
  });
});
