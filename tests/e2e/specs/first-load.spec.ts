import { expect, test } from '@playwright/test';

test('first load of the chat app completes under the 3 s budget', async ({ page }) => {
  const started = Date.now();
  await page.goto('/chat', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible();
  const elapsed = Date.now() - started;
  const navigation = await page.evaluate(() => {
    const [entry] = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
    return entry
      ? { domContentLoaded: entry.domContentLoadedEventEnd, loadEvent: entry.loadEventEnd }
      : null;
  });
  console.log(
    `first load: interactive after ${elapsed} ms; navigation timing ${JSON.stringify(navigation)}`,
  );
  expect(elapsed).toBeLessThan(3000);
});
