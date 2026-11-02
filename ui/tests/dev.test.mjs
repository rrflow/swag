import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseDevStatus } from '../dist/dev.js';

// Observe the actual unconfigured read model, never invent training measurements.
function currentStatus(recordedTraining = false) {
  const directory = mkdtempSync(join(tmpdir(), 'swag-status-'));
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('SWAG_')));
  env.SWAG_TRACE_DIR = directory;
  if (recordedTraining) env.SWAG_TRAINING_RUNS_FILE = fileURLToPath(new URL('../browser-tests/training-runs.json', import.meta.url));
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
  assert.equal(data.modelEndpoint.state, 'not_configured');
  assert.equal(data.modelEndpoint.modelListed, false);
  assert.equal(data.observability.measurements.length, 1);
  assert.equal(data.observability.measurements[0].operation, 'swag.model_endpoint');
  assert.equal(data.observability.measurements[0].errors, 0);
  assert.equal(data.observability.incompleteSpans, 0);
});

test('recorded real training history stays historical and rejects impossible progress', () => {
  const data = parseDevStatus(currentStatus(true));
  const progress = data.training.runs[0].progress;
  assert.equal(progress.globalStep, 33);
  assert.equal(progress.maxSteps, 33);
  assert.equal(progress.points.length, 37);
  assert.equal(data.training.launchAvailable, false);
  const changed = structuredClone(data);
  changed.training.runs[0].progress.globalStep = 34;
  assert.throws(() => parseDevStatus(changed));
  const badLoss = structuredClone(data);
  badLoss.training.runs[0].progress.points[0].loss = -1;
  assert.throws(() => parseDevStatus(badLoss));
});

test('UI rejects false readiness and invalid observation counts', () => {
  const original = currentStatus();
  for (const change of [
    data => { data.training.launchAvailable = true; },
    data => { data.integration.connectomeIntegrated = true; },
    data => { data.engine.authenticated = true; },
    data => { data.modelEndpoint.qualified = true; },
    data => { data.modelEndpoint.loadedWeightsVerified = true; },
    data => { data.modelEndpoint.inferencePerformed = true; },
    data => { data.modelEndpoint.modelListed = true; },
    data => { data.modelEndpoint.state = 'model_listed'; data.modelEndpoint.modelListed = true; },
    data => { data.training.dataset.state = 'verified_export'; },
    data => { data.observability.files = -1; },
    data => { data.observability.measurements = [null]; },
    data => { data.training.runs = [null]; },
  ]) {
    const changed = structuredClone(original); change(changed);
    assert.throws(() => parseDevStatus(changed));
  }
});
