import { expect, test, type Page } from '@playwright/test';

const source = 'https://example.com/primary-source';
const topic = {
  id: 'topic-1',
  title: 'AI engineering workflows',
  url: source,
  source: 'Primary publisher',
  excerpt: 'Source evidence for software engineering. '.repeat(15),
  category: 'architecture',
  priority: 90,
  status: 'queued',
  approved: false,
  verification: 'primary_source',
  published_at: '2026-10-07T10:00:00Z',
  retrieved_at: '2026-10-07T11:00:00Z',
  post_id: null,
  error: null,
};
const post = {
  id: 'post-1',
  title: 'Original developer analysis',
  caption: `Practical engineering guidance. Source: ${source}`,
  status: 'draft',
  version: '1',
  created: '2026-10-07T12:00:00Z',
  evidence: {
    source_url: source,
    source_title: topic.title,
    source_name: topic.source,
    published_at: topic.published_at,
    retrieved_at: topic.retrieved_at,
    excerpt: topic.excerpt,
    topic: 'architecture',
    editorial_angle: 'What should developers test?',
  },
  verification: { supported: true, issues: [], human_review_required: true },
  slides: Array.from({ length: 6 }, (_, index) => ({
    id: `slide-${index}`,
    position: index + 1,
    headline: `Principle ${index}`,
    body: 'Practical developer explanation.',
    has_artwork: true,
    composition_mode: 'ai_native',
    artwork_current: true,
    validation: {
      passed: true,
      issues: [],
      image_sha256: `image-${index}`,
      human_review_required: true,
    },
  })),
};
const blankJob = {
  id: 'job-1',
  kind: 'generate',
  status: 'queued',
  step: 'Waiting for worker',
  progress: 0,
  total: 6,
  attempts: 0,
  max_attempts: 3,
  available_at: new Date().toISOString(),
  created_at: '2026-10-07T23:00:00Z',
  finished_at: null,
  payload: {},
  result: null,
  error: null,
};

async function mockApi(
  page: Page,
  options: { draft?: boolean; publishing?: boolean; failed?: boolean; warnings?: boolean } = {},
) {
  let posts = options.draft ? [structuredClone(post)] : [];
  let topics = [structuredClone(topic)];
  let jobs: Record<string, unknown>[] = options.failed
    ? [{ ...blankJob, status: 'failed', error: 'Provider rate limit', kind: 'artwork' }]
    : options.warnings
      ? [
          {
            ...blankJob,
            kind: 'research',
            status: 'completed_with_warnings',
            step: 'Completed with source warnings',
            result: {
              created_topic_ids: ['topic-1'],
              skipped_urls: ['https://example.com/existing'],
              warnings: [
                'OpenAI News: article HTTP 403; insufficient readable source evidence (3 stories)',
              ],
            },
          },
        ]
      : [];
  const mutations: { path: string; body: unknown }[] = [];
  await page.route('http://127.0.0.1:8123/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    if (method === 'OPTIONS') {
      await route.fulfill({ status: 200 });
      return;
    }
    let result: unknown = {};
    if (method === 'GET') {
      if (path === '/auth/me')
        result = { id: 'test-admin', email: 'admin@example.test', role: 'admin' };
      else if (path.endsWith('/versions')) result = [];
      else if (path === '/posts') result = posts;
      else if (path === '/topics') result = topics;
      else if (path === '/jobs') result = jobs;
      else if (path === '/research/daily/latest')
        result = { run: null, topic: 'news', timezone: 'America/Chicago' };
      else if (path === '/workflow/config')
        result = {
          worker_enabled: true,
          daily_enabled: false,
          daily_hour: 8,
          timezone: 'America/Chicago',
          openai_configured: true,
          instagram_configured: Boolean(options.publishing),
          public_media_configured: Boolean(options.publishing),
        };
      else if (path.endsWith('/image')) {
        await route.fulfill({
          contentType: 'image/png',
          body: Buffer.from(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aV3cAAAAASUVORK5CYII=',
            'base64',
          ),
        });
        return;
      }
    } else {
      const body = request.postDataJSON() as unknown;
      mutations.push({ path, body });
      if (path.endsWith('/generate')) {
        posts = [structuredClone(post)];
        topics[0].status = 'used';
        jobs = [
          {
            ...blankJob,
            status: 'completed',
            progress: 6,
            step: 'Completed',
            result: { post_id: 'post-1' },
          },
        ];
        result = jobs[0];
      } else if (path.endsWith('/submit')) {
        posts[0].status = 'pending_review';
        result = { status: 'pending_review' };
      } else if (path.startsWith('/topics/') && path.endsWith('/approve')) {
        topics[0].approved = true;
        result = topics[0];
      } else if (path.endsWith('/approve')) {
        posts[0].status = 'approved';
        result = { status: 'approved' };
      } else if (path.endsWith('/publish')) {
        jobs = [{ ...blankJob, kind: 'publish', payload: { post_id: 'post-1', version: '1' } }];
        result = jobs[0];
      } else if (path.endsWith('/retry')) {
        jobs = [{ ...blankJob, kind: 'artwork', status: 'queued' }];
        result = jobs[0];
      } else if (path === '/research/refresh') {
        jobs = [
          {
            ...blankJob,
            kind: 'research',
            status: 'running',
            progress: 1,
            step: 'Checking primary-source evidence',
          },
        ];
        result = jobs[0];
      } else if (path === '/topics') {
        topics = [{ ...structuredClone(topic), ...(body as object), verification: 'unverified' }];
        result = topics[0];
      } else if (path.endsWith('/verify')) {
        topics[0].verification = 'human_verified';
        result = topics[0];
      }
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(result),
    });
  });
  return mutations;
}

test('preserves dashboard and exposes persistent research progress', async ({ page }) => {
  const calls = await mockApi(page);
  await page.goto('/');
  await expect(page.getByText('devai studio')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Overview', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Refresh research' }).click();
  await expect(page.getByText('Checking primary-source evidence', { exact: false })).toBeVisible();
  await expect(page.getByRole('progressbar', { name: 'research progress' })).toHaveAttribute(
    'value',
    '1',
  );
  expect(calls[0].path).toBe('/research/refresh');
  await page.screenshot({ path: 'test-results/dashboard-overview.png', fullPage: true });
});

test('manual evidence must be verified before selecting six-slide generation', async ({ page }) => {
  const calls = await mockApi(page);
  await page.goto('/');
  await page.getByLabel('Story headline').fill('Manual source for developers');
  await page.getByLabel('Primary source URL').fill(source);
  await page.getByLabel('Source excerpt (at least 240 characters)').fill(topic.excerpt);
  await page.getByRole('button', { name: 'Add source to queue' }).click();
  await page.getByRole('radio').check();
  await expect(page.getByRole('button', { name: 'Generate selected topic' })).toBeDisabled();
  await page.getByRole('button', { name: 'I reviewed and verified this evidence' }).click();
  await page.getByRole('button', { name: 'Approve topic', exact: true }).click();
  await page.getByLabel('Slides', { exact: true }).selectOption('6');
  await page.getByRole('button', { name: 'Generate selected topic' }).click();
  expect(calls.find((call) => call.path.endsWith('/generate'))?.body).toEqual({
    slide_count: 6,
    artwork: true,
  });
  await page.getByRole('button', { name: 'Review draft', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Review content' })).toBeVisible();
  await expect(page.getByText('Image validation passed.', { exact: false })).toBeVisible();
});

test('human review and configuration gate publishing from existing editor', async ({ page }) => {
  const calls = await mockApi(page, { draft: true, publishing: true });
  await page.goto('/');
  await page.getByRole('button', { name: /AI \/ ENGINEERING/ }).click();
  await page.getByRole('button', { name: 'Submit for review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Approve', exact: true })).toBeDisabled();
  await page
    .getByRole('checkbox', { name: 'I reviewed the sources, copy, code and all slide images.' })
    .check();
  await page.getByRole('button', { name: 'Approve', exact: true }).click();
  await page.getByRole('button', { name: 'Publish approved carousel to Instagram' }).click();
  expect(calls.map((call) => call.path)).toEqual([
    '/posts/post-1/submit',
    '/posts/post-1/approve',
    '/posts/post-1/publish',
  ]);
  await expect(page.getByRole('button', { name: 'Save post', exact: true })).toBeDisabled();
});

test('failed jobs can be retried visibly', async ({ page }) => {
  const calls = await mockApi(page, { failed: true });
  await page.goto('/');
  await page.getByRole('button', { name: 'Retry job', exact: true }).click();
  expect(calls[0].path).toBe('/jobs/job-1/retry');
  await expect(page.getByText('queued', { exact: true })).toBeVisible();
});

test('partial research shows warning status, topic counts and expandable source diagnostics', async ({
  page,
}) => {
  await mockApi(page, { warnings: true });
  await page.goto('/');
  await expect(page.getByText('completed with warnings', { exact: true })).toBeVisible();
  await expect(
    page.getByText('1 new topics added · 1 sources already queued or used'),
  ).toBeVisible();
  await expect(page.getByRole('progressbar', { name: 'research progress' })).toHaveAttribute(
    'value',
    '6',
  );
  await page.getByText('Source warnings (1)', { exact: true }).click();
  await expect(
    page.getByText(
      'OpenAI News: article HTTP 403; insufficient readable source evidence (3 stories)',
      { exact: true },
    ),
  ).toBeVisible();
});

for (const status of ['completed_with_warnings', 'running', 'failed']) {
  test(`latest ${status} refresh supersedes old daily warnings and retains dated history`, async ({
    page,
  }) => {
    await mockApi(page);
    await page.route('http://127.0.0.1:8123/research/daily/latest', async (route) => {
      await route.fulfill({
        json: {
          topic: 'news',
          timezone: 'America/Chicago',
          mode: 'research',
          run: {
            id: 'earlier-daily',
            local_date: '2026-10-07',
            timezone: 'America/Chicago',
            status: 'completed_with_warnings',
            attempt_count: 1,
            started_at: '2026-10-07T05:40:00Z',
            finished_at: '2026-10-07T05:41:00Z',
            retry_after: null,
            result: { warnings: ['GitHub Blog: ParseError'] },
            error: null,
          },
          latest_research: {
            ...blankJob,
            kind: 'research',
            status,
            step: 'Checking source evidence',
            error: status === 'failed' ? 'No usable evidence' : null,
            result:
              status === 'completed_with_warnings'
                ? {
                    created_topic_ids: ['topic-1'],
                    skipped_urls: [],
                    warnings: ['OpenAI News: article HTTP 403'],
                  }
                : null,
          },
        },
      });
    });
    await page.goto('/');
    const panel = page.getByRole('region', { name: 'AI news and developer impact' });
    await expect(panel.getByText('Latest research refresh ·', { exact: false })).toBeVisible();
    await expect(
      panel.getByText('Historical source warnings:', { exact: false }),
    ).not.toBeVisible();
    if (status === 'completed_with_warnings') {
      await expect(
        panel.getByText('1 new topics added · 0 sources already queued or used.', { exact: false }),
      ).toBeVisible();
      await panel.getByText('Latest refresh source warnings (1)').click();
      await expect(panel.getByText('OpenAI News: article HTTP 403', { exact: true })).toBeVisible();
    } else if (status === 'running') {
      await expect(panel.getByRole('button', { name: 'Researching…' })).toBeDisabled();
      await expect(panel.getByRole('status')).toContainText('Research refresh is in progress.');
    } else {
      await expect(panel.getByRole('button', { name: 'Retry research' })).toBeEnabled();
      await expect(panel.getByRole('status')).toContainText('No usable evidence');
    }
    await panel.getByText('Earlier daily run ·', { exact: false }).click();
    await expect(
      panel.getByText('Historical source warnings: GitHub Blog: ParseError'),
    ).toBeVisible();
  });
}

test('failed grounding jobs show claim-level evidence without exposing an approvable draft', async ({
  page,
}) => {
  await mockApi(page);
  await page.route('http://127.0.0.1:8123/jobs', async (route) => {
    await route.fulfill({
      json: [
        {
          ...blankJob,
          kind: 'generate',
          status: 'failed',
          error: 'Source grounding failed: 1 evidence quote does not match the saved source',
          result: {
            grounding: {
              supported: false,
              issues: ['Unsupported accuracy claim'],
              claims: [
                {
                  claim: 'The system reaches 99.9% accuracy',
                  evidence_quote: '99.9% accuracy',
                  evidence_matched: false,
                },
              ],
            },
          },
        },
      ],
    });
  });
  await page.goto('/');
  await page.getByText('Review grounding report', { exact: true }).click();
  await expect(page.getByRole('listitem').filter({ hasText: 'Claim 1:' })).toContainText(
    '99.9% accuracy',
  );
  await expect(
    page.getByText('Quote does not match saved evidence.', { exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: 'Review draft', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Retry job', exact: true })).toBeEnabled();
});
