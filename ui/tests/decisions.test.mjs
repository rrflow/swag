import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseDecisionLog, describe } from '../dist/decisions.js';

const python = process.env.SWAG_PYTHON ?? 'python';
const tool = name => fileURLToPath(new URL(`../../tools/${name}`, import.meta.url));

// Record real decisions through the CLI with no model configured, then read the actual log.
function recorded() {
  const directory = mkdtempSync(join(tmpdir(), 'swag-decisions-'));
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('SWAG_')));
  env.SWAG_DECISION_LOG = join(directory, 'log.jsonl'); env.SWAG_TRACE_DIR = join(directory, 'traces');
  try {
    execFileSync(python, [tool('swag.py'), 'decide', '--template', 'python_delivery_review', '--state', 'pyproject.toml'], { env, encoding: 'utf8' });
    return JSON.parse(execFileSync(python, [tool('swag_decision_log.py')], { env, encoding: 'utf8' }));
  } finally { rmSync(directory, { recursive: true, force: true }); }
}

test('a real decision without a model shows every mode abstaining for lack of an engine', () => {
  const data = parseDecisionLog(recorded());
  assert.equal(data.requests, 1);
  const questions = Object.values(data.records[0].questions);
  assert.deepEqual(new Set(questions.map(q => q.mode)), new Set(['binary', 'choice', 'score']));
  for (const question of questions) assert.equal(describe(question), 'Abstained: no engine');
  assert.equal(data.records[0].engine.consulted, false);
  assert.equal(data.records[0].suggestions.length, 3);
});

test('the UI refuses records that misstate who decided', () => {
  const data = recorded();
  for (const change of [
    x => { x.records[0].questions.dependency_separation.value = true; },
    x => { x.records[0].questions.test_organization.mode = 'ranking'; },
    x => { x.records[0].effectiveDigest = 'not-a-digest'; },
    x => { x.hopsMs.composeMs.median = 'fast'; },
  ]) {
    const changed = structuredClone(data); change(changed);
    assert.throws(() => parseDecisionLog(changed));
  }
});

test('a rule default says why SWAG abstained and never credits the model', () => {
  const question = { mode: 'choice', status: 'defaulted', value: 'security', option: 'security', reason: 'rule_default_on_abstain',
    abstainReason: 'no_engine', defaultedBy: 'never_alone_on_billing', rules: ['never_alone_on_billing'], skippedRules: [],
    preferences: [], instructions: 'Who should review it?' };
  assert.equal(describe(question), 'Abstained (no engine); rule never_alone_on_billing set "security"');
  assert.equal(describe({ ...question, status: 'required', reason: 'hard_rule' }), 'Hard rule never_alone_on_billing set "security"; model not asked');
});
