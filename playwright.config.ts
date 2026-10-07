import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './web/tests',
  fullyParallel: true,
  use: {
    baseURL: 'http://127.0.0.1:5181',
    channel: process.env.PLAYWRIGHT_CHROMIUM_CHANNEL || undefined,
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm --prefix web run dev -- --port 5181 --strictPort',
    url: 'http://127.0.0.1:5181',
    reuseExistingServer: false,
    env: { VITE_API_URL: 'http://127.0.0.1:8123' },
  },
});
