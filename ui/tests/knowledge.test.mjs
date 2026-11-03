import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseKnowledge, changedRequirements } from '../dist/knowledge.js';

function current() {
  const directory = mkdtempSync(join(tmpdir(), 'swag-knowledge-'));
  const binding = join(directory, 'binding.json');
  writeFileSync(binding, JSON.stringify({ schemaVersion: 1, projectId: 'swag',
    repo: fileURLToPath(new URL('../../', import.meta.url)), template: 'python_delivery_review',
    inputs: { packaging: ['requirements.txt'], tests: ['tests/test_swag_knowledge.py'], ci: ['.github/workflows/ci.yml'] } }));
  const env = { ...process.env, SWAG_TRACE_DIR: join(directory, 'traces') };
  try {
    return parseKnowledge(JSON.parse(execFileSync(process.env.SWAG_PYTHON ?? 'python',
      [fileURLToPath(new URL('../../tools/swag_knowledge.py', import.meta.url)), '--binding', binding], { env, encoding: 'utf8' })));
  } finally { rmSync(directory, { recursive: true, force: true }); }
}

test('actual repository template contains sourced requirements in all three modes', () => {
  const data = current();
  assert.equal(data.state, 'preview');
  assert.deepEqual(new Set(data.requirements.map(row => row.decision.mode)), new Set(['binary', 'choice', 'score']));
  assert.equal(data.fulfillmentAvailable, false);
  assert.deepEqual(changedRequirements(data, current()), []);
});

test('UI rejects fabricated fulfillment and malformed input/rubric projections', () => {
  const data = current();
  for (const change of [
    x => x.requirements[0].fulfillment = 'fulfilled',
    x => x.requirements[0].inputs.packaging[0].sha256 = null,
    x => x.requirements[2].decision.maximum = Number.NaN,
    x => x.requirements[1].decision.options[1].id = x.requirements[1].decision.options[0].id,
  ]) {
    const changed = structuredClone(data); change(changed);
    assert.throws(() => parseKnowledge(changed));
  }
});
