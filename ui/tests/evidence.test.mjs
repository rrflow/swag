import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseEvidence, outcome } from '../dist/evidence.js';
const load = () => JSON.parse(readFileSync(new URL('../public/evidence.json', import.meta.url)));
test('actual saved run retains failures and no execution authority', () => {
  const data = parseEvidence(load());
  assert.equal(data.metrics.cases, 13);
  assert.equal(data.metrics.matched, 7);
  assert.equal(data.authority.trainingAuthorized, false);
  assert.equal(data.cases.filter(row => outcome(row) === 'Policy violation').length, 5);
});
test('malformed projections cannot claim integration or qualification', () => {
  for (const mutate of [
    data => { data.authority.connectomeIntegrated = true; },
    data => { data.metrics.deploymentQualified = true; },
    data => { data.metrics.matched = 13; },
    data => { data.metrics.warmMedianSeconds = -1; },
    data => { data.cases[0].caseRef = data.cases[1].caseRef; },
    data => { data.provenance.protocolSha256 = 'unknown'; },
  ]) {
    const data = load(); mutate(data); assert.throws(() => parseEvidence(data));
  }
});
