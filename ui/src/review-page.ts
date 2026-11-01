import { loadPacket, newDecisions, parseReview, validDecision, type Packet, type Decision, type Review } from './review.js';
const el = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
let packet: Packet | undefined;
let packetSha = '';
let decisions: Decision[] = [];
let index = 0;
let dirty = false;
let loadGeneration = 0;
const report = (message: string) => { el('review-error').textContent = message; el('review-error').hidden = !message; };
function render() {
  if (!packet) return;
  const entry = packet.tasks[index]!;
  const task = entry.task, decision = decisions[index]!;
  el('packet-id').textContent = packetSha;
  el('task-position').textContent = `Task ${index + 1} of ${packet.tasks.length}`;
  el('task-title').textContent = task.input;
  el('task-id').textContent = task.taskId;
  el('proposed').textContent = `Proposed: ${task.provisionalLabel ?? 'unknown'} · ${task.labelOrigin}`;
  const source = el<HTMLAnchorElement>('source-link');
  const match = /^([\w.-]+\/[\w.-]+)#(\d+)$/.exec(task.taskId);
  source.hidden = !match;
  if (match) source.href = `https://github.com/${match[1]}/pull/${match[2]}`;
  el<HTMLSelectElement>('decision').value = decision.decision;
  el<HTMLSelectElement>('label').value = decision.label ?? '';
  el<HTMLSelectElement>('label').disabled = decision.decision !== 'correct';
  el<HTMLTextAreaElement>('rationale').value = decision.rationale;
  el<HTMLTextAreaElement>('references').value = decision.evidenceRefs.join('\n');
  el('model-outputs').replaceChildren(...Object.entries(entry.outcomes).map(([name, output]) => {
    const section = document.createElement('section');
    const heading = document.createElement('h3'); heading.textContent = name;
    const pre = document.createElement('pre'); pre.textContent = JSON.stringify(output, null, 2);
    section.append(heading, pre); return section;
  }));
  el<HTMLButtonElement>('previous').disabled = index === 0;
  el<HTMLButtonElement>('next').disabled = index === packet.tasks.length - 1;
  progress();
}
function progress() {
  if (!packet) return;
  const complete = decisions.filter((d, i) => validDecision(d, packet!.tasks[i]!.task)).length;
  el('review-progress').textContent = `${complete}/${decisions.length} decisions complete${dirty ? ' · Unsaved changes' : ''}`;
  el<HTMLButtonElement>('export-complete').disabled = complete !== decisions.length;
  el<HTMLButtonElement>('export-draft').disabled = false;
}
function update() {
  if (!packet) return;
  const d = decisions[index]!, task = packet.tasks[index]!.task;
  d.decision = el<HTMLSelectElement>('decision').value as Decision['decision'];
  d.label = d.decision === 'accept' ? task.provisionalLabel : d.decision === 'correct' ? el<HTMLSelectElement>('label').value || null : null;
  d.rationale = el<HTMLTextAreaElement>('rationale').value;
  d.evidenceRefs = el<HTMLTextAreaElement>('references').value.split('\n').map(s => s.trim()).filter(Boolean);
  el<HTMLSelectElement>('label').disabled = d.decision !== 'correct';
  if (d.decision !== 'correct') el<HTMLSelectElement>('label').value = d.label ?? '';
  dirty = true; progress();
}
async function install(bytes: Uint8Array, expected: string, generation: number) {
  const parsed = await loadPacket(bytes, expected);
  if (generation !== loadGeneration) return;
  packet = parsed; packetSha = expected; decisions = newDecisions(parsed); index = 0; dirty = false;
  el('review-workspace').hidden = false; report(''); render();
}
for (const id of ['decision','label','rationale','references']) el(id).addEventListener('input', update);
for (const id of ['reviewer','reviewer-kind','label-author']) el(id).addEventListener('input', () => { dirty = true; progress(); });
el('previous').addEventListener('click', () => { index--; render(); });
el('next').addEventListener('click', () => { index++; render(); });
function download(complete: boolean) {
  try {
    if (!packet) return;
    const value: Review = { schemaVersion: 1, purpose: 'development_label_review', packetSha256: packetSha,
      reviewerId: el<HTMLInputElement>('reviewer').value.trim(), reviewerKind: el<HTMLSelectElement>('reviewer-kind').value as Review['reviewerKind'],
      labelAuthorId: el<HTMLInputElement>('label-author').value.trim(), reviewedAt: new Date().toISOString(), decisions };
    parseReview(value, packet, packetSha, complete);
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2) + '\n'], { type: 'application/json' }));
    const a = document.createElement('a'); a.href = url; a.download = `swag-review-${packetSha}.json`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000); dirty = false; progress(); report('');
  } catch (error) { report((error as Error).message); }
}
el('export-draft').addEventListener('click', () => download(false));
el('export-complete').addEventListener('click', () => download(true));
el<HTMLInputElement>('resume-review').addEventListener('change', async event => {
  const file = (event.target as HTMLInputElement).files?.[0]; if (!file || !packet) return;
  try {
    if (file.size > 5_000_000) throw new Error('Review is too large.');
    const boundPacket = packet, boundSha = packetSha;
    const value = parseReview(JSON.parse(await file.text()), boundPacket, boundSha);
    if (boundPacket !== packet) throw new Error('Packet changed during review import.');
    if (dirty && !confirm('Replace your unsaved decisions with this review file?')) return;
    const byId = new Map(value.decisions.map(d => [d.taskId, d]));
    decisions = packet.tasks.map(entry => byId.get(entry.task.taskId)!);
    el<HTMLInputElement>('reviewer').value = value.reviewerId;
    el<HTMLSelectElement>('reviewer-kind').value = value.reviewerKind;
    el<HTMLInputElement>('label-author').value = value.labelAuthorId;
    dirty = false; report(''); render();
  } catch (error) { report((error as Error).message); }
  finally { (event.target as HTMLInputElement).value = ''; }
});
el<HTMLInputElement>('packet-import').addEventListener('change', async event => {
  const input = event.target as HTMLInputElement, file = input.files?.[0]; if (!file) return;
  try {
    if (dirty && !confirm('Open a different packet and discard unsaved decisions? Download your draft first to keep it.')) return;
    if (file.size > 5_000_000 || !/^[a-f0-9]{64}\.json$/.test(file.name)) throw new Error('Import the engine packet using its SHA-256 filename.');
    const generation = ++loadGeneration;
    await install(new Uint8Array(await file.arrayBuffer()), file.name.slice(0, -5), generation);
  } catch (error) { report((error as Error).message); }
  finally { input.value = ''; }
});
window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
try {
  const generation = ++loadGeneration;
  const response = await fetch('./review-source.json'); if (!response.ok) throw new Error('Import a review packet to begin.');
  const source = await response.json() as { packetSha256: string; labelAuthorId: string };
  const data = await fetch('./review-packet.json'); if (!data.ok) throw new Error('Review packet unavailable.');
  const bytes = new Uint8Array(await data.arrayBuffer());
  await install(bytes, source.packetSha256, generation);
  if (generation === loadGeneration) el<HTMLInputElement>('label-author').value = source.labelAuthorId;
} catch (error) { report((error as Error).message); }
