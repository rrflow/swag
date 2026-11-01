export type Task = { taskId: string; project: string; sourceSha256: string; input: string; labelOrigin: string; provisionalLabel: string | null };
export type Packet = { schemaVersion: number; tasks: { task: Task; outcomes: Record<string, unknown>; reviewState: string }[]; sourceManifest: { candidates: { candidateId: string }[] }; trainingAdmitted: false; deploymentQualified: false; reviewState: string };
export type Decision = { taskId: string; decision: 'pending' | 'accept' | 'correct' | 'exclude'; label: string | null; rationale: string; evidenceRefs: string[] };
export type Review = { schemaVersion: 1; purpose: 'development_label_review'; packetSha256: string; reviewerId: string; reviewerKind: 'human' | 'assistant'; labelAuthorId: string; reviewedAt: string; decisions: Decision[] };
const sha = /^[a-f0-9]{64}$/;
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const text = (v: unknown): v is string => typeof v === 'string' && v.trim().length > 0 && v.length <= 2048;
export async function loadPacket(bytes: Uint8Array, expected: string): Promise<Packet> {
  if (bytes.length > 5_000_000 || !sha.test(expected)) throw new Error('Invalid packet size or expected digest.');
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new Uint8Array(bytes)))).map(n => n.toString(16).padStart(2, '0')).join('');
  if (digest !== expected) throw new Error('Packet bytes do not match the expected digest.');
  const value: unknown = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  if (!object(value) || value.schemaVersion !== 1 || value.trainingAdmitted !== false || value.deploymentQualified !== false || value.reviewState !== 'pending_independent_review' || !Array.isArray(value.tasks) || !value.tasks.length || value.tasks.length > 10000 || !object(value.sourceManifest) || !Array.isArray(value.sourceManifest.candidates)) throw new Error('Invalid pending review packet.');
  const candidates = value.sourceManifest.candidates.map(c => {
    if (!object(c) || !text(c.candidateId)) throw new Error('Invalid candidate.'); return c.candidateId;
  });
  if (candidates.length < 2 || candidates.length > 16 || new Set(candidates).size !== candidates.length) throw new Error('Invalid candidate coverage.');
  const seen = new Set<string>();
  for (const entry of value.tasks) {
    if (!object(entry) || !object(entry.task) || !object(entry.outcomes) || entry.reviewState !== 'pending_independent_review') throw new Error('Invalid task record.');
    const t = entry.task;
    if (!text(t.taskId) || seen.has(t.taskId) || !text(t.project) || !text(t.input) || !text(t.labelOrigin) || !text(t.sourceSha256) || !sha.test(t.sourceSha256) || !(t.provisionalLabel === null || text(t.provisionalLabel))) throw new Error('Invalid or duplicate task.');
    seen.add(t.taskId);
    if (Object.keys(entry.outcomes).length !== candidates.length || candidates.some(c => !Object.hasOwn(entry.outcomes as object, c))) throw new Error('Incomplete paired outcomes.');
  }
  return value as unknown as Packet;
}
export function newDecisions(packet: Packet): Decision[] {
  return packet.tasks.map(({ task }) => ({ taskId: task.taskId, decision: 'pending', label: null, rationale: '', evidenceRefs: [`source:${task.sourceSha256}`] }));
}
export function validDecision(decision: Decision, task: Task): boolean {
  if (!text(decision.rationale) || !Array.isArray(decision.evidenceRefs) || !decision.evidenceRefs.length || decision.evidenceRefs.length > 16 || !decision.evidenceRefs.every(text)) return false;
  if (decision.decision === 'exclude') return decision.label === null;
  if (!text(decision.label)) return false;
  return decision.decision === 'accept' ? decision.label === task.provisionalLabel : decision.decision === 'correct' && decision.label !== task.provisionalLabel;
}
export function parseReview(value: unknown, packet: Packet, packetSha256: string, complete = false): Review {
  if (!object(value) || Object.keys(value).sort().join(',') !== ['schemaVersion','purpose','packetSha256','reviewerId','reviewerKind','labelAuthorId','reviewedAt','decisions'].sort().join(',') || value.schemaVersion !== 1 || value.purpose !== 'development_label_review' || value.packetSha256 !== packetSha256 || !text(value.reviewerId) || !text(value.labelAuthorId) || value.reviewerId.trim().toLowerCase() === value.labelAuthorId.trim().toLowerCase() || !['human','assistant'].includes(String(value.reviewerKind)) || typeof value.reviewedAt !== 'string' || !/(Z|[+-]\d\d:\d\d)$/.test(value.reviewedAt) || !Number.isFinite(Date.parse(value.reviewedAt)) || Date.parse(value.reviewedAt) > Date.now() || !Array.isArray(value.decisions) || value.decisions.length !== packet.tasks.length) throw new Error('Review identity, timestamp, packet binding or task count is invalid.');
  const seen = new Set<string>();
  const tasks = new Map(packet.tasks.map(e => [e.task.taskId, e.task]));
  for (const d of value.decisions) {
    if (!object(d) || Object.keys(d).sort().join(',') !== ['taskId','decision','label','rationale','evidenceRefs'].sort().join(',') || !text(d.taskId) || seen.has(d.taskId) || !tasks.has(d.taskId) || !['pending','accept','correct','exclude'].includes(String(d.decision)) || !(d.label === null || text(d.label)) || typeof d.rationale !== 'string' || d.rationale.length > 2048 || !Array.isArray(d.evidenceRefs) || d.evidenceRefs.length > 16 || !d.evidenceRefs.every(text)) throw new Error('Invalid or duplicate review decision.');
    seen.add(d.taskId);
    if (complete && !validDecision(d as Decision, tasks.get(d.taskId)!)) throw new Error('Complete every task with a decision, rationale and evidence reference.');
  }
  return value as unknown as Review;
}
