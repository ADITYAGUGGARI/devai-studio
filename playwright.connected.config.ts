import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './web/tests/connected',
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:5182',
    channel: process.env.PLAYWRIGHT_CHROMIUM_CHANNEL || undefined,
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'PYTHONPATH=api/src .venv/bin/python scripts/e2e_server.py',
      url: 'http://127.0.0.1:8124/ready',
      reuseExistingServer: false,
    },
    {
      command: 'npm --prefix web run dev -- --port 5182 --strictPort',
      url: 'http://127.0.0.1:5182',
      reuseExistingServer: false,
      // Deliberately differ from the UI's loopback host to guard cookie auth.
      env: { VITE_API_URL: 'http://localhost:8124' },
    },
  ],
});
