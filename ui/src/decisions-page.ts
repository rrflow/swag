import { parseDecisionLog, describe } from './decisions.js';
const container = document.getElementById('decisions')!;
const button = document.getElementById('refresh-decisions') as HTMLButtonElement;
const add = (parent: HTMLElement, tag: string, value: string, className?: string) => {
  const node = document.createElement(tag); node.textContent = value; if (className) node.className = className; parent.append(node); return node;
};
const row = (body: HTMLElement, values: (string | number)[]) => {
  const tr = document.createElement('tr'); for (const value of values) add(tr, 'td', String(value)); body.append(tr);
};
const table = (parent: HTMLElement, headings: string[]) => {
  const scroll = document.createElement('div'); scroll.className = 'scroll';
  const element = document.createElement('table'); const head = document.createElement('thead'); const tr = document.createElement('tr');
  for (const heading of headings) add(tr, 'th', heading);
  head.append(tr); const body = document.createElement('tbody'); element.append(head, body); scroll.append(element); parent.append(scroll);
  return body;
};
const HOPS: Record<string, string> = { composeMs: 'Compose (layers, facts)', engineMs: 'Model', decideMs: 'Decide (rules, preferences, suggestions)' };

async function refresh() {
  button.disabled = true;
  try {
    const response = await fetch('/api/dev/decisions', { cache: 'no-store' });
    if (!response.ok) throw new Error('Unavailable');
    const data = parseDecisionLog(await response.json());
    container.replaceChildren();
    if (data.state === 'empty') {
      add(container, 'p', 'No decisions recorded yet. Run `python tools/swag.py decide --template python_delivery_review --state "..."` or send a request to the SWAG server.');
      return;
    }
    add(container, 'p', `${data.requests} decision requests in the local log.`);
    const modes = table(container, ['Mode', 'Answered', 'Abstained', 'Required by rule', 'Defaulted by rule', 'Median confidence']);
    for (const mode of ['binary', 'choice', 'score']) {
      const counts = data.byMode[mode] ?? {};
      row(modes, [mode, counts.answered ?? 0, counts.abstained ?? 0, counts.required ?? 0, counts.defaulted ?? 0,
        data.confidence[mode] ? data.confidence[mode].median.toFixed(2) : 'n/a']);
    }
    const hops = table(container, ['Step', 'Samples', 'Median ms', 'p95 ms']);
    for (const [key, value] of Object.entries(data.hopsMs)) row(hops, [HOPS[key] ?? key, value.samples, value.median.toFixed(1), value.p95.toFixed(1)]);
    for (const record of data.records) {
      const article = document.createElement('article'); article.className = 'run';
      const engine = record.engine.consulted ? `${record.engine.model} via ${record.engine.protocol}${record.engine.rotations ? ' with rotations' : ''}` : 'no model consulted';
      add(article, 'h3', `${new Date(record.at).toLocaleString()} · ${record.template ?? record.source} · ${engine}`);
      add(article, 'p', Object.entries(record.timings).map(([key, ms]) => `${HOPS[key] ?? key} ${ms.toFixed(1)} ms`).join(' · '), 'note');
      for (const [id, question] of Object.entries(record.questions)) {
        const block = document.createElement('div'); block.className = 'decision';
        add(block, 'h4', `${id} · ${question.mode}`);
        add(block, 'p', question.instructions);
        add(block, 'p', describe(question));
        const details = document.createElement('details'); add(details, 'summary', 'Why: rules, preferences and probabilities');
        if (question.rules.length) add(details, 'p', `Rules applied: ${question.rules.join(', ')}`);
        for (const skipped of question.skippedRules) add(details, 'p', `Rule ${skipped.rule} skipped: ${skipped.reason.replaceAll('_', ' ')}${skipped.fact ? ` (${skipped.fact})` : ''}`);
        for (const preference of question.preferences) add(details, 'p', `Preference ${preference.key} = ${JSON.stringify(preference.value)} from ${preference.layer ?? 'default'}${preference.reason ? ` (${preference.reason.replaceAll('_', ' ')})` : ''}`);
        if (question.forbidden?.length) add(details, 'p', `Forbidden by rule: ${question.forbidden.join(', ')}`);
        if (question.answer) add(details, 'p', `Model answer: ${JSON.stringify(question.answer)}`);
        if (question.engineMs !== undefined) add(details, 'p', `Model time ${question.engineMs.toFixed(1)} ms`);
        block.append(details); article.append(block);
      }
      if (record.suggestions.length) {
        add(article, 'h4', 'Suggestions');
        for (const suggestion of record.suggestions) add(article, 'p', `${suggestion.byRule ? 'Rule' : 'Suggested'} · ${suggestion.question}: ${suggestion.text}`);
      }
      if (record.staleFacts.length) add(article, 'p', `Stale facts not used: ${record.staleFacts.join(', ')}`, 'note');
      add(article, 'p', `Effective layers ${record.effectiveDigest.slice(0, 12)} · state ${record.stateChars} characters, ${record.stateSha256.slice(0, 12)}`, 'note');
      container.append(article);
    }
  } catch {
    container.replaceChildren(); add(container, 'p', 'Decision log unavailable. Check SWAG_DECISION_LOG and local traces.');
  } finally { button.disabled = false; }
}
button.addEventListener('click', refresh);
void refresh();
