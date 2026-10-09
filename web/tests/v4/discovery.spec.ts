import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('real PostgreSQL discovery preview is responsive and accessible', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/');
  await page
    .getByRole('navigation', { name: 'Main navigation' })
    .getByRole('button', { name: 'Research' })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Developer AI news · Last 24 hours' }),
  ).toBeVisible();
  await expect(page.getByText('Loading research history…')).not.toBeVisible();
  await page.screenshot({ path: 'test-results/v4-discovery-desktop.png', fullPage: true });
  const desktop = await new AxeBuilder({ page }).analyze();
  expect(desktop.violations).toEqual([]);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole('heading', { name: 'Developer AI news · Last 24 hours' }),
  ).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.screenshot({ path: 'test-results/v4-discovery-phone.png', fullPage: true });
  const phone = await new AxeBuilder({ page }).analyze();
  expect(phone.violations).toEqual([]);
});
