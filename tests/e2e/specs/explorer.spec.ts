import { expect, test } from '@playwright/test';

test('explorer: search a company, open it and see history vs QTD on the chart', async ({
  page,
}) => {
  await page.goto('/explore');
  await page.getByLabel('Search companies').fill('orbitly');
  await expect(page.getByRole('link', { name: /ORBY/ })).toBeVisible();
  await page.getByRole('link', { name: /ORBY/ }).click();

  await expect(page.getByRole('heading', { name: /Orbitly Analytics/ })).toBeVisible();
  const chart = page.getByTestId('kpi-chart');
  await expect(chart).toBeVisible();
  await expect(chart).toHaveAttribute('data-points', '15'); // 14 historical + 1 QTD marker
  await expect(page.getByText('as of 2026-09-15')).toBeVisible();
  await expect(page.getByLabel('History table').locator('tbody tr')).toHaveCount(14);
  await page.getByRole('tab', { name: /Customer Churn/ }).click();
  await expect(page.getByLabel('History table').locator('tbody tr')).toHaveCount(14);
});

test('explorer: an unknown sector filter shows a problem banner from the API', async ({ page }) => {
  await page.goto('/explore');
  await page.getByLabel('Search companies').fill('zzzz');
  await expect(page.getByText(/No company matched/)).toBeVisible();
});
