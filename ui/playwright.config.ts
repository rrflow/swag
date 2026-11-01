import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './browser-tests',
  use: { baseURL: 'http://127.0.0.1:8891', headless: true },
  webServer: { command: 'npm run dev', url: 'http://127.0.0.1:8891', reuseExistingServer: !process.env.CI },
});
