import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('workspace research schedule persists and retains edits across a competing device', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Use an existing local account' }).click();
  await page.getByLabel('Email address', { exact: true }).fill('e2e@devai.test');
  await page.getByLabel('Password', { exact: true }).fill('Isolated-e2e-password-12345');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Settings', exact: true }).first().click();
  await page.getByRole('button', { name: 'Research schedule', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Research schedule', exact: true })).toBeVisible();
  await page.getByLabel('Daily research', { exact: true }).check();
  await page.getByLabel('Research time', { exact: true }).fill('07:45');
  await page.getByLabel('Research timezone', { exact: true }).fill('Asia/Kolkata');
  await page.getByRole('button', { name: 'Save schedule', exact: true }).click();
  await expect(page.getByRole('status').filter({ hasText: /^Saved$/ })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Research timezone', { exact: true })).toHaveValue('Asia/Kolkata');
  await expect(page.getByLabel('Research time', { exact: true })).toHaveValue('07:45');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: 'test-results/connected/research-schedule-desktop.png',
    fullPage: true,
  });
  const login = await request.post('http://127.0.0.1:8124/auth/login', {
    data: { email: 'e2e@devai.test', password: 'Isolated-e2e-password-12345' },
  });
  const headers = { Authorization: `Bearer ${(await login.json()).token}` };
  const account = await request.get('http://127.0.0.1:8124/auth/me', { headers });
  const workspaceId = (await account.json()).workspace_id;
  const url = `http://127.0.0.1:8124/v1/workspaces/${workspaceId}/settings`;
  const value = await (await request.get(url, { headers })).json();
  await page.getByLabel('Daily research', { exact: true }).uncheck();
  const external = await request.patch(url, {
    headers: { ...headers, 'Idempotency-Key': 'second-device-schedule' },
    data: {
      expectedRevision: value.revision,
      researchEnabled: true,
      researchLocalTime: '09:15',
      timeZone: value.timeZone,
      categories: value.categories,
      autoDraftOptions: { enabled: false },
    },
  });
  expect(external.ok()).toBeTruthy();
  await page.getByRole('button', { name: 'Save schedule', exact: true }).click();
  await expect(
    page.getByText('This schedule changed on another device.', { exact: false }),
  ).toBeVisible();
  await expect(page.getByLabel('Daily research', { exact: true })).not.toBeChecked();
  await page.getByRole('button', { name: 'Keep my changes against latest revision' }).click();
  await page.getByRole('button', { name: 'Save schedule', exact: true }).click();
  await expect(page.getByRole('status').filter({ hasText: /^Saved$/ })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Daily research', { exact: true })).not.toBeChecked();
  await page.setViewportSize({ width: 390, height: 844 });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({
    path: 'test-results/connected/research-schedule-phone.png',
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Run research now', exact: true }).click();
  await expect(page).toHaveURL(/\/discover\?run=/);
  const runId = new URL(page.url()).searchParams.get('run');
  const run = await request.get(`http://127.0.0.1:8124/v1/research/runs/${runId}`, { headers });
  expect(run.ok()).toBeTruthy();
  const snapshot = await run.json();
  expect(snapshot.job.status).toBe('queued');
  expect(
    new Date(snapshot.windowEndUTC).valueOf() - new Date(snapshot.windowStartUTC).valueOf(),
  ).toBe(24 * 60 * 60 * 1000);
  const cancelled = await request.post(`http://127.0.0.1:8124/v1/jobs/${snapshot.jobId}/cancel`, {
    headers,
  });
  expect(cancelled.ok()).toBeTruthy();
});
