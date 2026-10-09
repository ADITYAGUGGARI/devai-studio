// Read-only visual acceptance of the real local workspace. No approval/publication.
import { chromium } from '@playwright/test';
import { readFile, mkdir } from 'node:fs/promises';
const values = Object.fromEntries(
  (await readFile('.local-data/admin-login.txt', 'utf8'))
    .trim()
    .split('\n')
    .map((line) => {
      const i = line.indexOf(':');
      return [line.slice(0, i).trim().toLowerCase(), line.slice(i + 1).trim()];
    }),
);
const browser = await chromium.launch({
  channel: process.env.PLAYWRIGHT_CHROMIUM_CHANNEL || 'chrome',
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await page.goto('http://localhost:5173');
await page.getByLabel('Email', { exact: true }).fill(values.email);
await page.getByLabel('Password', { exact: true }).fill(values.password);
await page.getByRole('button', { name: 'Sign in', exact: true }).click();
await page.getByRole('heading', { name: 'Your studio, today' }).waitFor();
await mkdir('.local-data/live-acceptance/browser', { recursive: true });
await page.screenshot({ path: '.local-data/live-acceptance/browser/overview.png', fullPage: true });
await page.getByRole('button', { name: 'Research', exact: true }).first().click();
await page.getByRole('heading', { name: 'Prioritized topic queue' }).waitFor();
await page.screenshot({
  path: '.local-data/live-acceptance/browser/research-desktop.png',
  fullPage: true,
});
await page.getByRole('button', { name: 'Library', exact: true }).first().click();
await page
  .getByRole('button', { name: /Designing Smart Content Ingestion for Generative AI Systems/ })
  .click();
await page.getByRole('heading', { name: 'Review content' }).waitFor();
await page.getByRole('img').first().waitFor();
await page.screenshot({
  path: '.local-data/live-acceptance/browser/review-desktop.png',
  fullPage: true,
});
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({
  path: '.local-data/live-acceptance/browser/review-phone.png',
  fullPage: true,
});
console.log(
  'Real workspace login, research overview and image review rendered on desktop and phone widths.',
);
await page.getByRole('button', { name: 'Sign out', exact: true }).click();
await browser.close();
