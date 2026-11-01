import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { loadPacket, newDecisions, parseReview, validDecision } from '../dist/review.js';
const bytes = new Uint8Array(readFileSync(new URL('../public/review-packet.json', import.meta.url)));
const source = JSON.parse(readFileSync(new URL('../public/review-source.json', import.meta.url)));
const load = () => loadPacket(bytes, source.packetSha256);
const review = packet => ({ schemaVersion: 1, purpose: 'development_label_review', packetSha256: source.packetSha256,
  reviewerId: 'test-only-reviewer', reviewerKind: 'assistant', labelAuthorId: source.labelAuthorId,
  reviewedAt: new Date().toISOString(), decisions: newDecisions(packet) });
test('actual packet is verified and all 63 outcomes remain available', async () => {
  const packet = await load(); assert.equal(packet.tasks.length, 21);
  assert.equal(packet.tasks.flatMap(e => Object.keys(e.outcomes)).length, 63);
  await assert.rejects(loadPacket(bytes, '0'.repeat(64)));
  const changed = new Uint8Array(bytes); changed[20] ^= 1;
  await assert.rejects(loadPacket(changed, source.packetSha256));
});
test('pending drafts resume but cannot finalize; explicit completed exclusions can', async () => {
  const packet = await load(), value = review(packet);
  assert.equal(parseReview(value, packet, source.packetSha256).decisions.length, 21);
  assert.throws(() => parseReview(value, packet, source.packetSha256, true));
  for (const d of value.decisions) { d.decision = 'exclude'; d.rationale = 'Synthetic UI test only'; }
  assert.equal(parseReview(value, packet, source.packetSha256, true).decisions.length, 21);
});
test('wrong packet, duplicate task, fabricated fields and author self-review reject', async () => {
  const packet = await load();
  for (const mutate of [v => v.packetSha256 = '0'.repeat(64), v => v.reviewerId = source.labelAuthorId,
    v => v.decisions[1] = v.decisions[0], v => v.trainingAdmitted = true, v => v.reviewerKind = 'verified']) {
    const value = review(packet); mutate(value); assert.throws(() => parseReview(value, packet, source.packetSha256));
  }
});
test('accept and correction have different semantics', async () => {
  const packet = await load(), task = packet.tasks[0].task, d = newDecisions(packet)[0];
  d.rationale = 'Test evidence'; d.decision = 'accept'; d.label = task.provisionalLabel;
  assert.equal(validDecision(d, task), true);
  d.decision = 'correct'; assert.equal(validDecision(d, task), false);
  d.label = task.provisionalLabel === 'implementation' ? 'documentation' : 'implementation';
  assert.equal(validDecision(d, task), true);
});
