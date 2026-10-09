import { defineConfig } from '@playwright/test';

export default defineConfig({
  outputDir: 'test-results/v4',
  testDir: './web/tests/v4',
  fullyParallel: false,
  timeout: 45000,
  use: {
    baseURL: 'http://127.0.0.1:5185',
    channel: process.env.PLAYWRIGHT_CHROMIUM_CHANNEL || undefined,
    trace: 'retain-on-failure',
  },
});
