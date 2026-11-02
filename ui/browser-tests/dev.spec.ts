import { test, expect } from '@playwright/test';

test('developer UI renders actual read model and keeps launch unavailable', async ({ page, request }) => {
  const status = await request.get('/api/dev/status');
  expect(status.status()).toBe(200);
  expect((await status.json()).schema).toBe('swag.dev-status/v1');
  await page.goto('/dev.html');
  await expect(page.locator('#observed')).toContainText('Observed');
  await expect(page.getByRole('button', { name: 'Launch training' })).toBeDisabled();
  await expect(page.locator('#error')).toBeHidden();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Refresh observations' }).click();
  await expect(page.getByRole('button', { name: 'Refresh observations' })).toBeEnabled();
  await expect(page.locator('#error')).toBeHidden();
});

test('developer API is read-only and rejects cross-origin requests', async ({ request }) => {
  expect((await request.post('/api/dev/status')).status()).toBe(405);
  expect((await request.get('/api/dev/status', { headers: { Origin: 'https://example.com' } })).status()).toBe(403);
  expect((await request.get('/api/dev/status', { headers: { Host: 'example.com' } })).status()).toBe(403);
});
