import { expect, test } from '@playwright/test';

test.describe('chat workflow: user question -> LLM -> MCP tool -> database -> answer', () => {
  test('asks a QTD question and sees the tool call with its arguments and the cited answer', async ({
    page,
  }) => {
    await page.goto('/chat');
    await page.getByLabel('Ask a question').fill("What's ORBY's QTD total revenue this quarter?");
    await page.getByRole('button', { name: 'Send' }).click();

    const panel = page.getByLabel('Tool execution');
    await expect(panel.getByTestId('tool-call-card').first()).toBeVisible();
    await expect(panel.getByText('get_kpi_qtd', { exact: true })).toBeVisible();
    await expect(panel.getByText('ticker=ORBY')).toBeVisible();
    await expect(panel.getByText('kpi=total_revenue')).toBeVisible();
    await expect(panel.getByText('ok', { exact: true }).first()).toBeVisible();

    const answer = page.getByLabel('Assistant answer').last();
    await expect(answer).toContainText('2026-09-15');
    await expect(answer).toContainText('ORBY');
    await expect(panel.getByText(/trace [0-9a-f]{16}/)).toBeVisible();
  });

  test('shows the result preview when a tool card is expanded', async ({ page }) => {
    await page.goto('/chat');
    await page.getByText('Show ORBY total revenue history').click();
    const panel = page.getByLabel('Tool execution');
    await expect(panel.getByText('get_kpi_history', { exact: true })).toBeVisible();
    await expect(page.getByLabel('Assistant answer').last()).toContainText('2026Q2');
    await panel.getByRole('button', { expanded: false }).first().click();
    await expect(panel.getByTestId('result-preview')).toContainText('total_revenue');
  });
});
