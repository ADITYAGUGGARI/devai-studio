import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const email = 'e2e@devai.test';
const password = 'Isolated-e2e-password-12345';
test('real PostgreSQL accounts, editorial queue, version recovery and accessibility', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'Your next great story starts here.' }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await expect(page).toHaveScreenshot('login.png');
  await page.getByRole('button', { name: 'Use an existing local account' }).click();
  await page.getByLabel('Email address', { exact: true }).fill(email);
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
  await page.getByRole('button', { name: 'Open editorial topic queue' }).click();
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
  await page
    .getByLabel('Headline', { exact: true })
    .fill('Unsaved slide kept while saving caption');
  await page.getByRole('tab', { name: 'Copy', exact: true }).click();
  await page.getByLabel('Caption', { exact: true }).fill('Updated manual draft caption.');
  await page.getByRole('button', { name: 'Save post', exact: true }).click();
  await expect(page.getByText('Post details · v2')).toBeVisible();
  await page.getByRole('tab', { name: 'Slide', exact: true }).click();
  await expect(page.getByLabel('Headline', { exact: true })).toHaveValue(
    'Unsaved slide kept while saving caption',
  );
  await expect(page.getByRole('button', { name: 'Submit for review', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Save slide', exact: true }).click();
  await expect(page.getByText('Unsaved edits ·', { exact: false })).toHaveCount(0);
  await page.getByRole('tab', { name: 'History', exact: true }).click();
  await page.getByText('Version history', { exact: true }).click();
  await page.getByRole('button', { name: 'Restore version 1 as draft' }).click();
  await page.getByRole('tab', { name: 'Copy', exact: true }).click();
  await expect(page.getByLabel('Caption', { exact: true })).toHaveValue(
    'Manual copy for version recovery testing.',
  );
  await expect(page.getByText('Post details · v4')).toBeVisible();
  await page.getByRole('button', { name: 'Submit for review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Approve', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Settings', exact: true }).first().click();
  await expect(page.getByText('postgresql', { exact: false }).first()).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await expect(page).toHaveScreenshot('operations.png', {
    fullPage: true,
    // Other real journeys create durable job history; compare layout independently of its counts.
    mask: [page.locator('.source-evidence').filter({ hasText: 'Background work' }).locator('span')],
  });
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Your next great story starts here.' }),
  ).toBeVisible();
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
  await page.getByRole('button', { name: 'Use an existing local account' }).click();
  await page.getByLabel('Email address', { exact: true }).fill(email);
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

test('real settings persist and administrator-created viewer cannot create drafts', async ({
  page,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Use an existing local account' }).click();
  await page.getByLabel('Email address', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Settings', exact: true }).first().click();
  await page.getByRole('button', { name: 'Daily research', exact: true }).click();
  await page.getByLabel('Hour (0–23)', { exact: true }).fill('9');
  await page.getByLabel('Timezone', { exact: true }).fill('UTC');
  await page.getByRole('button', { name: 'Save research schedule', exact: true }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Workspace updated.' })).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: 'Settings', exact: true }).first().click();
  await page.getByRole('button', { name: 'Daily research', exact: true }).click();
  await expect(page.getByLabel('Hour (0–23)', { exact: true })).toHaveValue('9');
  await expect(page.getByLabel('Timezone', { exact: true })).toHaveValue('UTC');
  await page.getByRole('button', { name: 'Accounts', exact: true }).click();
  await page.getByLabel('Account email', { exact: true }).fill('viewer-ux@devai.test');
  await page.getByLabel('Initial password', { exact: true }).fill('Isolated-viewer-password-12345');
  await page.getByLabel('Role', { exact: true }).selectOption('viewer');
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await expect(page.getByText('Account created.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await page.getByRole('button', { name: 'Use an existing local account' }).click();
  await page.getByLabel('Email address', { exact: true }).fill('viewer-ux@devai.test');
  await page.getByLabel('Password', { exact: true }).fill('Isolated-viewer-password-12345');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Library', exact: true }).first().click();
  await expect(page.getByRole('button', { name: '+ New draft', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Research', exact: true }).first().click();
  await page.getByRole('button', { name: 'Open editorial topic queue' }).click();
  await expect(
    page.getByRole('button', { name: 'Add your own source', exact: true }),
  ).toBeDisabled();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test('profile saves across reload and competing device edits require explicit conflict resolution', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Use an existing local account' }).click();
  await page.getByLabel('Email address', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Settings', exact: true }).first().click();
  await page.getByRole('button', { name: 'Profile & preferences', exact: true }).click();
  await expect(page).toHaveURL(/\/settings\/profile$/);
  await page.getByLabel('Display name', { exact: true }).fill('Studio engineer');
  await page.getByLabel('Personal timezone', { exact: true }).fill('Asia/Kolkata');
  await page.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Save profile', exact: true })).toBeDisabled();
  await page.reload();
  await expect(page.getByLabel('Display name', { exact: true })).toHaveValue('Studio engineer');
  await page.getByLabel('Display name', { exact: true }).fill('My local edits');
  const login = await request.post('http://127.0.0.1:8124/auth/login', {
    data: { email, password },
  });
  const headers = { Authorization: `Bearer ${(await login.json()).token}` };
  const profile = await request.get('http://127.0.0.1:8124/v1/me', { headers });
  const current = await profile.json();
  const changed = await request.patch('http://127.0.0.1:8124/v1/me', {
    headers: { ...headers, 'Idempotency-Key': 'browser-second-device-profile' },
    data: {
      displayName: 'Other device edits',
      timeZone: 'UTC',
      locale: 'en',
      expectedRevision: current.revision,
    },
  });
  expect(changed.ok()).toBeTruthy();
  await page.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Profile conflict' })).toBeVisible();
  await expect(page.getByLabel('Display name', { exact: true })).toHaveValue('My local edits');
  await page.getByRole('button', { name: 'Keep my changes for a new save' }).click();
  await page.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Save profile', exact: true })).toBeDisabled();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: 'test-results/profile-desktop.png', fullPage: true });
});
