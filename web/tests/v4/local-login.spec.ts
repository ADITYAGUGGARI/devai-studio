import { test, expect } from '@playwright/test';

test('local review origin supports real cookie sign-in and authenticated reads', async ({
  page,
}) => {
  test.skip(
    !process.env.LOCAL_REVIEW_EMAIL || !process.env.LOCAL_REVIEW_PASSWORD,
    'Requires an explicitly configured local review account',
  );
  await page.goto('http://127.0.0.1:5187/');
  await page.getByRole('button', { name: 'Use an existing local account' }).click();
  await page.getByLabel('Email address', { exact: true }).fill(process.env.LOCAL_REVIEW_EMAIL!);
  await page.getByLabel('Password', { exact: true }).fill(process.env.LOCAL_REVIEW_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
  await page.getByRole('button', { name: 'Settings', exact: true }).first().click();
  await page.getByRole('button', { name: 'Profile & preferences', exact: true }).click();
  await expect(page.getByLabel('Display name', { exact: true })).toBeVisible();
  await expect(
    page.getByText(process.env.LOCAL_REVIEW_EMAIL!, { exact: true }).last(),
  ).toBeVisible();
});
