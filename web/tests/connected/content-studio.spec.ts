import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function signIn(page: import('@playwright/test').Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Use an existing local account' }).click();
  await page.getByLabel('Email address', { exact: true }).fill('e2e@devai.test');
  await page.getByLabel('Password', { exact: true }).fill('Isolated-e2e-password-12345');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Your studio, today', exact: true }),
  ).toBeVisible();
}

test('persisted content setup connects topic approval, configuration, and credential failure', async ({
  page,
  request,
}) => {
  const login = await request.post('http://127.0.0.1:8124/auth/login', {
    data: { email: 'e2e@devai.test', password: 'Isolated-e2e-password-12345' },
  });
  const headers = { Authorization: `Bearer ${(await login.json()).token}` };
  const source = await request.post('http://127.0.0.1:8124/topics', {
    headers,
    data: {
      title: 'Creation setup integration test source',
      url: 'https://example.com/test-only-create-workflow',
      excerpt:
        'This is isolated test-only source evidence for developer workflow configuration. '.repeat(
          12,
        ),
      category: 'architecture',
    },
  });
  expect(source.ok()).toBeTruthy();
  const id = (await source.json()).id;
  expect(
    (await request.post(`http://127.0.0.1:8124/topics/${id}/verify`, { headers })).ok(),
  ).toBeTruthy();
  expect(
    (await request.post(`http://127.0.0.1:8124/topics/${id}/approve`, { headers })).ok(),
  ).toBeTruthy();
  await signIn(page);
  await page.goto('/create');
  await page.getByLabel('Approved topic').selectOption(id);
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page).toHaveURL(/\/create\/.+\/configure$/);
  await page.getByLabel('Audience', { exact: true }).fill('Backend engineers');
  await page.getByLabel('Tone', { exact: true }).selectOption('Analytical');
  await page.getByRole('button', { name: 'Save & review generation' }).click();
  await expect(page.getByRole('button', { name: 'Confirm & generate' })).toBeDisabled();
  await expect(page.getByText('Generation is unavailable.', { exact: false })).toBeVisible();
  const setupId = page.url().match(/\/create\/([^/]+)/)![1];
  const saved = await request.get(`http://127.0.0.1:8124/v1/setups/${setupId}`, { headers });
  expect((await saved.json()).data.options.audience).toBe('Backend engineers');
  await page.reload();
  await expect(page.getByLabel('Audience', { exact: true })).toHaveValue('Backend engineers');
  await expect(page.getByLabel('Tone', { exact: true })).toHaveValue('Analytical');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: 'test-results/connected/create-configure-desktop.png',
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
  await page.screenshot({
    path: 'test-results/connected/create-configure-phone.png',
    fullPage: true,
  });
});

test('actual rendered Reel plays, autosaves, retains old media and recovers a competing edit', async ({
  page,
  request,
}) => {
  test.skip(
    process.env.E2E_REEL_FIXTURE !== 'true',
    'Requires explicitly enabled isolated codec fixture',
  );
  await signIn(page);
  await page.goto('/content');
  await page.getByRole('button', { name: /Reel codec acceptance fixture/ }).click();
  await expect(page.getByLabel('Rendered Reel preview')).toBeVisible();
  expect(
    await page.getByLabel('Rendered Reel preview').evaluate((video: HTMLVideoElement) => ({
      width: video.videoWidth,
      height: video.videoHeight,
    })),
  ).toEqual({ width: 1080, height: 1920 });
  await page.getByLabel('Rendered Reel preview').evaluate((video: HTMLVideoElement) => {
    video.currentTime = 12;
  });
  await page.getByLabel('Scene duration in seconds').fill('6.5');
  await expect(page.getByRole('status').filter({ hasText: /^Saved$/ })).toBeVisible();
  await expect(page.getByText('Previous render preserved', { exact: false })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Scene duration in seconds')).toHaveValue('6.5');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: 'test-results/connected/reel-editor-desktop.png', fullPage: true });
  const projectId = page.url().match(/\/studio-content\/([^?]+)/)![1];
  const login = await request.post('http://127.0.0.1:8124/auth/login', {
    data: { email: 'e2e@devai.test', password: 'Isolated-e2e-password-12345' },
  });
  const headers = { Authorization: `Bearer ${(await login.json()).token}` };
  const project = await (
    await request.get(`http://127.0.0.1:8124/v1/content/${projectId}`, { headers })
  ).json();
  const output = project.outputs[0];
  await page.getByLabel('Headline', { exact: true }).fill('My retained device edit');
  const external = await request.patch(`http://127.0.0.1:8124/v1/outputs/${output.id}/timeline`, {
    headers: { ...headers, 'Idempotency-Key': 'reel-second-device' },
    data: {
      expectedRevision: output.revision,
      scenes: output.data.scenes.map(
        ({
          id,
          headline,
          body,
          script,
          durationSec,
        }: {
          id: string;
          headline: string;
          body: string;
          script: string;
          durationSec: number;
        }) => ({ id, headline, body, script, durationSec }),
      ),
      caption: output.data.caption + '\nSecond device analysis.',
      voiceId: null,
      subtitles: false,
    },
  });
  expect(external.ok()).toBeTruthy();
  await expect(
    page.getByRole('heading', { name: 'This timeline changed on another device' }),
  ).toBeVisible();
  await expect(page.getByLabel('Headline', { exact: true })).toHaveValue('My retained device edit');
  await page.getByRole('button', { name: 'Keep my changes and save against this version' }).click();
  await page.getByRole('button', { name: 'Save now', exact: true }).click();
  await expect(page.getByRole('status').filter({ hasText: /^Saved$/ })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
  await page.screenshot({ path: 'test-results/connected/reel-editor-phone.png', fullPage: true });
  await page.getByRole('button', { name: 'Version history', exact: true }).click();
  await page.getByRole('button', { name: 'Restore version 2', exact: true }).click();
  const restoreResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith('/versions/restore') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Restore as a new draft', exact: true }).click();
  expect((await restoreResponse).ok()).toBeTruthy();
  await expect(page.getByText('Previous render preserved', { exact: false })).toHaveCount(0);
  const restored = await request.get(`http://127.0.0.1:8124/v1/outputs/${output.id}`, { headers });
  const restoredOutput = await restored.json();
  expect(restoredOutput.data.renderCurrent).toBeTruthy();
  expect(restoredOutput.data.approval).toBeUndefined();
  expect(restoredOutput.revision).toBeGreaterThan(output.revision);
});
