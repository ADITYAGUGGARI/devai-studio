import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const email = 'e2e@devai.test';
const password = 'Isolated-e2e-password-12345';
test('real PostgreSQL accounts, editorial queue, version recovery and accessibility', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Welcome back.' })).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await expect(page).toHaveScreenshot('login.png');
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByText('devai studio')).toBeVisible();
  await page.reload();
  await expect(page.getByText('devai studio')).toBeVisible();
  await page.screenshot({ path: 'test-results/overview-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole('heading', { name: 'Give your next story the final touch.' }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.screenshot({ path: 'test-results/overview-phone.png', fullPage: true });
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.getByRole('button', { name: 'Research', exact: true }).first().click();
  await page.getByText('Add your own source', { exact: true }).click();
  await page.getByLabel('Story headline').fill('Isolated browser test: source retrieval contract');
  await page.getByLabel('Primary source URL').fill('https://example.test/e2e-source');
  await page
    .getByLabel('Source excerpt (at least 240 characters)')
    .fill(
      'This is explicitly isolated test evidence for the editorial workflow, not a real news announcement. '.repeat(
        6,
      ),
    );
  await page.getByRole('button', { name: 'Add source to queue' }).click();
  await page.getByRole('button', { name: 'I reviewed and verified this evidence' }).click();
  await page.getByRole('button', { name: 'Approve topic', exact: true }).click();
  await page.getByRole('radio').check();
  await expect(page.getByRole('button', { name: 'Generate selected topic' })).toBeEnabled();
  const login = await request.post('http://127.0.0.1:8124/auth/login', {
    data: { email, password },
  });
  expect(login.ok()).toBeTruthy();
  const token = (await login.json()).token;
  const headers = { Authorization: `Bearer ${token}` };
  const topics = await request.get('http://127.0.0.1:8124/topics', { headers });
  expect((await topics.json())[0].approved).toBe(true);
  const draft = await request.post('http://127.0.0.1:8124/posts', {
    headers,
    data: {
      title: 'Isolated editorial draft',
      caption: 'Manual copy for version recovery testing.',
      slides: Array.from({ length: 8 }, (_, i) => ({
        headline: `Manual slide ${i + 1}`,
        body: 'Explicit test copy. No provider output is simulated.',
      })),
    },
  });
  expect(draft.ok()).toBeTruthy();
  await page.getByRole('button', { name: 'Library', exact: true }).first().click();
  await page.getByRole('button', { name: /Isolated editorial draft/ }).click();
  await page.getByRole('tab', { name: 'Copy', exact: true }).click();
  await page.getByLabel('Caption', { exact: true }).fill('Updated manual draft caption.');
  await page.getByRole('button', { name: 'Save post', exact: true }).click();
  await expect(page.getByText('Post details · v2')).toBeVisible();
  await page.getByRole('tab', { name: 'History', exact: true }).click();
  await page.getByText('Version history', { exact: true }).click();
  await page.getByRole('button', { name: 'Restore version 1 as draft' }).click();
  await page.getByRole('tab', { name: 'Copy', exact: true }).click();
  await expect(page.getByLabel('Caption', { exact: true })).toHaveValue(
    'Manual copy for version recovery testing.',
  );
  await expect(page.getByText('Post details · v3')).toBeVisible();
  await page.getByRole('button', { name: 'Submit for review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Approve', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Settings', exact: true }).first().click();
  await expect(page.getByText('postgresql', { exact: false }).first()).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await expect(page).toHaveScreenshot('operations.png', { fullPage: true });
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back.' })).toBeVisible();
  expect((await page.request.get('http://127.0.0.1:8124/posts')).status()).toBe(401);
});

test('real generated eight-image artifact can be reviewed, exported and invalidated in an isolated workspace', async ({
  page,
}) => {
  test.skip(
    !process.env.LIVE_CAROUSEL_FIXTURE,
    'Requires a real provider artifact created by scripts/live_acceptance.py',
  );
  await page.goto('/');
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Library', exact: true }).first().click();
  await page
    .getByRole('button', { name: /Designing Smart Content Ingestion for Generative AI Systems/ })
    .click();
  await expect(page.getByRole('img').first()).toBeVisible();
  await page.getByRole('button', { name: 'Submit for review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Approve', exact: true })).toBeDisabled();
  await page
    .getByRole('checkbox', { name: 'I reviewed the sources, copy, code and all slide images.' })
    .check();
  await page.getByRole('button', { name: 'Approve', exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Publish approved carousel to Instagram' }),
  ).toBeDisabled();
  const exported = page.waitForEvent('download');
  await page.getByRole('button', { name: /Download.*PNG ZIP/ }).click();
  const file = await exported;
  expect(file.suggestedFilename()).toMatch(/\.zip$/);
  expect(await file.failure()).toBeNull();
  await page.screenshot({ path: 'test-results/real-provider-review.png', fullPage: true });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole('tab', { name: 'Copy', exact: true }).click();
  await page
    .getByLabel('Caption', { exact: true })
    .fill('A changed caption invalidates the reviewed version.');
  await page.getByRole('button', { name: 'Save post', exact: true }).click();
  await expect(
    page.getByText('Current copy needs source grounding before approval.'),
  ).toBeVisible();
  await page.getByRole('tab', { name: 'History', exact: true }).click();
  await page.getByText('Version history', { exact: true }).click();
  await page.getByRole('button', { name: 'Restore version 1 as draft' }).click();
  await page.getByRole('tab', { name: 'Approval', exact: true }).click();
  await expect(
    page.getByRole('checkbox', {
      name: 'I reviewed the sources, copy, code and all slide images.',
    }),
  ).not.toBeChecked();
});
