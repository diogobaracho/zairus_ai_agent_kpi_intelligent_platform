import { expect, test } from '@playwright/test';

test('chat history survives a reload and the trace page shows the audit rows', async ({ page }) => {
  await page.goto('/chat');
  await page.getByLabel('Ask a question').fill('Which KPIs does KSTL publish?');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect(
    page.getByLabel('Tool execution').getByText('list_company_kpis', { exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel('Assistant answer').last()).toContainText('KSTL');
  // The usage line renders only after the `final` event, i.e. once the message is persisted.
  await expect(page.getByLabel('Tool execution').getByText(/tool call/)).toBeVisible();

  await page.reload();
  await expect(page.getByLabel('Assistant answer').last()).toContainText('KSTL');
  await expect(
    page.getByLabel('Tool execution').getByText('list_company_kpis', { exact: true }),
  ).toBeVisible();

  await page.getByRole('link', { name: /audit/ }).click();
  await expect(page.getByRole('heading', { name: /Audit trail/ })).toBeVisible();
  const rows = page.getByLabel('Audit rows').locator('tbody tr');
  await expect(rows.first()).toContainText('list_company_kpis');
  await expect(rows.first()).toContainText('agent');
});
