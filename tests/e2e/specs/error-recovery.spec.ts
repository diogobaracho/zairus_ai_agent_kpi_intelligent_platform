import { expect, test } from '@playwright/test';

test('a misspelled ticker produces a visible error step with a suggestion, then a successful retry', async ({
  page,
}) => {
  await page.goto('/chat');
  await page.getByLabel('Ask a question').fill('Show ORBYY revenue history');
  await page.getByRole('button', { name: 'Send' }).click();

  const panel = page.getByLabel('Tool execution');
  const cards = panel.getByTestId('tool-call-card');
  await expect(cards).toHaveCount(2);
  await expect(cards.nth(0).getByText('error', { exact: true })).toBeVisible();
  await expect(cards.nth(0).getByText('company_not_found')).toBeVisible();
  await expect(cards.nth(0).getByText('ORBY', { exact: true })).toBeVisible(); // suggestion chip
  await expect(cards.nth(1).getByText('ok', { exact: true })).toBeVisible();
  await expect(cards.nth(1).getByText('ticker=ORBY')).toBeVisible();
  await expect(page.getByLabel('Assistant answer').last()).toContainText('2023Q1');
});

test('a KPI that is not published for a company is explained, not hidden', async ({ page }) => {
  await page.goto('/chat');
  await page.getByLabel('Ask a question').fill('What is GAPW ARR QTD?');
  await page.getByRole('button', { name: 'Send' }).click();
  const panel = page.getByLabel('Tool execution');
  await expect(panel.getByText('kpi_not_found')).toBeVisible();
  await expect(page.getByLabel('Assistant answer').last()).toContainText(/No QTD|not published/i);
});
