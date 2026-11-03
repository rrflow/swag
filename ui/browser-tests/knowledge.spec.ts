import { test, expect } from '@playwright/test';
import { mkdtemp, mkdir, copyFile, writeFile, appendFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:net';
import { spawn } from 'node:child_process';
import { once } from 'node:events';

test('real source preview survives an ordinary edit without claiming fulfillment', async ({ page }, testInfo) => {
  test.setTimeout(60000);
  const root = fileURLToPath(new URL('../../', import.meta.url));
  const directory = await mkdtemp(join(tmpdir(), 'swag-template-browser-'));
  const probe = createServer();
  probe.listen(0, '127.0.0.1'); await once(probe, 'listening');
  const address = probe.address();
  if (!address || typeof address === 'string') throw new Error('No local port');
  const port = address.port; await new Promise<void>(resolve => probe.close(() => resolve()));
  const files = ['requirements.txt', 'tests/test_swag_knowledge.py', '.github/workflows/ci.yml'];
  for (const path of files) {
    await mkdir(resolve(directory, path, '..'), { recursive: true });
    await copyFile(join(root, path), join(directory, path));
  }
  const binding = join(directory, 'binding.json');
  await writeFile(binding, JSON.stringify({ schemaVersion: 1, projectId: 'swag-repository-copy', repo: '.',
    template: 'python_delivery_review', inputs: { packaging: [files[0]], tests: [files[1]], ci: [files[2]] } }));
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('SWAG_')));
  Object.assign(env, { SWAG_UI_PORT: String(port), SWAG_KNOWLEDGE_BINDING_FILE: binding,
    SWAG_TRACE_DIR: join(directory, 'traces'), SWAG_PYTHON: process.env.SWAG_PYTHON ?? 'python' });
  const child = spawn(process.execPath, [join(root, 'ui/scripts/serve.mjs')], { env, windowsHide: true, stdio: 'ignore' });
  const origin = `http://127.0.0.1:${port}`;
  const pageErrors: string[] = [];
  page.on('pageerror', e => pageErrors.push(e.message));
  try {
    await expect.poll(async () => { try { return (await fetch(origin + '/dev.html')).status; } catch { return 0; } }).toBe(200);
    await page.goto(origin + '/dev.html');
    await expect(page.locator('#knowledge article')).toHaveCount(3);
    const before = await (await page.request.get(origin + '/api/dev/knowledge')).json();
    expect(before.state).toBe('preview');
    for (const mode of ['binary', 'choice', 'score']) await expect(page.locator('#knowledge h3').filter({ hasText: mode })).toHaveCount(1);
    await page.locator('#knowledge summary').first().click();
    await expect(page.locator('#knowledge')).toContainText('https://packaging.python.org/');
    await appendFile(join(directory, files[0]), '\n# Development tooling separation remains under review.\n');
    await page.getByRole('button', { name: 'Refresh template inputs' }).click();
    await expect(page.locator('#knowledge')).toContainText('1 requirement has changed inputs');
    await expect(page.locator('[data-requirement="dependency_separation"]')).toContainText('Inputs changed');
    const after = await (await page.request.get(origin + '/api/dev/knowledge')).json();
    expect(after.requirements[0].inputSha256).not.toBe(before.requirements[0].inputSha256);
    expect(after.requirements.slice(1)).toEqual(before.requirements.slice(1));
    expect(after.requirements.every((r: { fulfillment: string }) => r.fulfillment === 'unassessed')).toBe(true);
    expect((await page.request.post(origin + '/api/dev/knowledge')).status()).toBe(405);
    expect((await page.request.get(origin + '/api/dev/knowledge', { headers: { Origin: 'https://example.com' } })).status()).toBe(403);
    await page.locator('#knowledge').screenshot({ path: testInfo.outputPath('knowledge-template.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.getByRole('button', { name: 'Refresh template inputs' }).click();
    await expect(page.locator('#knowledge')).toContainText('0 requirements have changed inputs');
    expect(pageErrors).toEqual([]);
  } finally {
    const exited = once(child, 'exit'); child.kill(); await exited;
    await rm(directory, { recursive: true, force: true });
  }
});
