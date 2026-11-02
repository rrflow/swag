import { defineConfig } from '@playwright/test';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  testDir: './browser-tests',
  use: { baseURL: 'http://127.0.0.1:8891', headless: true },
  webServer: { command: 'npm run dev', url: 'http://127.0.0.1:8891', reuseExistingServer: !process.env.CI,
    env: { SWAG_TRAINING_RUNS_FILE: fileURLToPath(new URL('./browser-tests/training-runs.json', import.meta.url)) } },
});
