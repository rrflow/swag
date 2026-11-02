import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseDevStatus } from '../dist/dev.js';

// Observe the actual unconfigured read model, never invent training measurements.
function currentStatus() {
  const directory = mkdtempSync(join(tmpdir(), 'swag-status-'));
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('SWAG_')));
  env.SWAG_TRACE_DIR = directory;
  try {
    return JSON.parse(execFileSync(process.env.SWAG_PYTHON ?? 'python',
      [fileURLToPath(new URL('../../tools/swag_dev_status.py', import.meta.url))], { env, encoding: 'utf8' }));
  } finally { rmSync(directory, { recursive: true, force: true }); }
}

test('actual unconfigured status cannot claim training, integration or usage', () => {
  const data = parseDevStatus(currentStatus());
  assert.equal(data.engine.authenticated, false);
  assert.equal(data.training.launchAvailable, false);
  assert.equal(data.training.dataset.state, 'not_configured');
  assert.deepEqual(data.training.runs, []);
  assert.deepEqual(data.observability.measurements, []);
  assert.equal(data.observability.incompleteSpans, 0);
});

test('UI rejects false readiness and invalid observation counts', () => {
  const original = currentStatus();
  for (const change of [
    data => { data.training.launchAvailable = true; },
    data => { data.integration.connectomeIntegrated = true; },
    data => { data.engine.authenticated = true; },
    data => { data.training.dataset.state = 'verified_export'; },
    data => { data.observability.files = -1; },
    data => { data.observability.measurements = [null]; },
    data => { data.training.runs = [null]; },
  ]) {
    const changed = structuredClone(original); change(changed);
    assert.throws(() => parseDevStatus(changed));
  }
});
