import { parseKnowledge, changedRequirements, type KnowledgePreview } from './knowledge.js';
const container = document.getElementById('knowledge')!;
const button = document.getElementById('refresh-knowledge') as HTMLButtonElement;
let previous: KnowledgePreview | undefined;
const paragraph = (parent: HTMLElement, value: string) => { const p = document.createElement('p'); p.textContent = value; parent.append(p); };
async function refresh() {
  button.disabled = true;
  try {
    const response = await fetch('/api/dev/knowledge', { cache: 'no-store' });
    if (!response.ok) throw new Error('Unavailable');
    const data = parseKnowledge(await response.json());
    container.replaceChildren();
    if (data.state !== 'preview') {
      paragraph(container, data.state === 'not_configured' ? 'No project template is bound. Configure a project binding to inspect its requirements.' : 'The project template could not be read. Check its binding and local traces.');
      previous = undefined;
      return;
    }
    const changed = new Set(changedRequirements(previous, data));
    paragraph(container, `${data.title} · ${data.projectId}`);
    paragraph(container, previous ? `${changed.size} ${changed.size === 1 ? 'requirement has' : 'requirements have'} changed inputs since the previous preview.` : 'Current project inputs loaded. No decisions have been assessed.');
    for (const row of data.requirements) {
      const article = document.createElement('article'); article.className = 'run'; article.dataset.requirement = row.id;
      const h = document.createElement('h3'); h.textContent = `${row.title} · ${row.decision.mode}`; article.append(h);
      paragraph(article, `${row.state === 'missing_inputs' ? 'Missing project inputs' : 'Inputs available'} · Fulfillment unassessed${changed.has(row.id) ? ' · Inputs changed' : ''}`);
      paragraph(article, row.decision.proposition ?? row.decision.question ?? row.decision.rubric!);
      for (const option of row.decision.options ?? []) paragraph(article, option.description);
      if (row.decision.mode === 'score') paragraph(article, `Scale ${row.decision.minimum}–${row.decision.maximum} · ${row.decision.direction?.replaceAll('_', ' ')}`);
      const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = 'Inspect practice and bound inputs'; details.append(summary);
      paragraph(details, row.practice.question.text);
      paragraph(details, `Source reference: ${JSON.stringify(row.practice.question.source)}. Freshness has not been reverified.`);
      for (const [slot, files] of Object.entries(row.inputs)) paragraph(details, `${slot}: ${files.map(f => `${f.path} (${f.state})`).join(', ') || 'No files bound'}`);
      paragraph(details, `Input revision: ${row.inputSha256}`);
      article.append(details); container.append(article);
    }
    previous = data;
  } catch {
    container.replaceChildren(); paragraph(container, 'Knowledge preview unavailable. Inspect the configured inputs and local traces.'); previous = undefined;
  } finally { button.disabled = false; }
}
button.addEventListener('click', refresh);
refresh();
