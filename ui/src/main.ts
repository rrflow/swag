import { parseEvidence, outcome, type Evidence } from './evidence.js';
function element<T extends HTMLElement = HTMLElement>(id: string): T {
  const result = document.getElementById(id);
  if (!result) throw new Error('Missing view element');
  return result as T;
}
function node(tag: string, text: string, className = ''): HTMLElement {
  const result = document.createElement(tag); result.textContent = text; result.className = className; return result;
}
let evidence: Evidence | undefined;
let filter = 'all';
function renderCases(): void {
  if (!evidence) return;
  const rows = evidence.cases.filter(row => filter === 'all' || (filter === 'matched' ? row.matched : !row.matched));
  element('case-count').textContent = `${rows.length} of ${evidence.cases.length} cases`;
  element('cases').replaceChildren(...rows.map(row => {
    const tr = node('tr', '');
    tr.append(node('td', row.caseRef, 'mono'));
    const status = node('td', ''); status.append(node('span', outcome(row), `badge ${row.matched ? 'success' : 'danger'}`));
    tr.append(status, node('td', `${row.elapsedSeconds.toFixed(2)} s`, 'mono')); return tr;
  }));
}
function render(data: Evidence): void {
  evidence = data;
  element('error').hidden = true;
  element('model').textContent = `${data.model.name} · ${data.model.precision.toUpperCase()}`;
  element('run-date').textContent = new Date(data.completedAt).toLocaleString();
  element('scope').textContent = `${data.scope} evidence`;
  const m = data.metrics;
  const cards = [
    ['Matched decisions', `${(m.accuracy * 100).toFixed(1)}%`, `${m.matched} of ${m.cases} cases`, 'teal'],
    ['Policy violations', String(m.policyViolations), 'In supplied eligibility constraints', 'red'],
    ['Warm median', m.warmMedianSeconds === null ? 'Unknown' : `${m.warmMedianSeconds.toFixed(2)} s`, `p95 ${m.p95Seconds.toFixed(2)} s · serial requests`, ''],
    ['Output validity', `${m.cases - m.invalidOutputs}/${m.cases}`, 'Valid format does not mean correct', '']
  ];
  element('metrics').replaceChildren(...cards.map(([label, value, note, tone]) => {
    const card = node('article', '', 'metric'); card.append(node('p', label!), node('strong', value!, tone), node('small', note!)); return card;
  }));
  element('signals').replaceChildren(...data.signals.map(signal => {
    const card = node('div', '', 'signal'); card.append(node('strong', String(signal.score), 'red'), node('p', signal.summary)); return card;
  }));
  if (!data.signals.length) element('signals').append(node('p', 'No rules matched. This is not deployment qualification.'));
  element('provenance').replaceChildren(...Object.entries(data.provenance).flatMap(([key, value]) => [node('dt', key), node('dd', value, 'mono')]));
  renderCases();
}
function showError(): void { element('error').hidden = false; element('error').textContent = 'Could not load a valid offline evidence export. The previous view, if present, is unchanged.'; }
document.querySelectorAll<HTMLButtonElement>('[data-filter]').forEach(button => button.addEventListener('click', () => {
  filter = button.dataset.filter ?? 'all';
  document.querySelectorAll<HTMLButtonElement>('[data-filter]').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
  renderCases();
}));
element<HTMLInputElement>('import').addEventListener('change', async event => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  try { if (file.size > 5_000_000) throw new Error('Too large'); render(parseEvidence(JSON.parse(await file.text()))); }
  catch { showError(); }
});
try {
  const response = await fetch('./evidence.json');
  if (!response.ok) throw new Error('Missing default evidence');
  render(parseEvidence(await response.json()));
} catch { showError(); }

try {
  const response = await fetch('./comparison.json');
  if (!response.ok) throw new Error('Missing comparison');
  const value: unknown = await response.json();
  if (!Array.isArray(value) || value.length < 2 || value.length > 10) throw new Error('Invalid comparison');
  const runs = value.map(parseEvidence);
  if (new Set(runs.map(run => run.provenance.protocolSha256)).size !== 1) throw new Error('Different protocols');
  element('comparison-rows').replaceChildren(...runs.map(run => {
    const row = node('tr', '');
    row.append(node('td', run.model.name), node('td', `${run.metrics.matched}/${run.metrics.cases}`),
      node('td', String(run.metrics.policyViolations)),
      node('td', run.metrics.warmMedianSeconds === null ? 'Unknown' : `${(run.metrics.warmMedianSeconds * 1000).toFixed(0)} ms`));
    return row;
  }));
} catch { element('comparison-status').textContent = 'Comparison unavailable or evidence does not share one protocol.'; }

try {
  const response = await fetch('./intent-comparison.json');
  const data = await response.json() as { scope?: unknown; deploymentQualified?: unknown; results?: unknown };
  if (!response.ok || data.scope !== 'provisional_intent_development' || data.deploymentQualified !== false ||
      !Array.isArray(data.results) || data.results.length > 10) throw new Error('Invalid intent evidence');
  const rows = data.results.map((value: unknown) => {
    if (!value || typeof value !== 'object') throw new Error('Invalid intent row');
    const row = value as Record<string, unknown>;
    if (typeof row.model !== 'string' || row.model.length > 200 ||
        typeof row.cases !== 'number' || !Number.isInteger(row.cases) || row.cases < 1 ||
        typeof row.matched !== 'number' || !Number.isInteger(row.matched) || row.matched < 0 || row.matched > row.cases ||
        typeof row.balancedAccuracy !== 'number' || !Number.isFinite(row.balancedAccuracy) ||
        row.balancedAccuracy < 0 || row.balancedAccuracy > 1) throw new Error('Invalid intent metrics');
    const tr = node('tr', '');
    tr.append(node('td', row.model), node('td', `${row.matched}/${row.cases}`),
      node('td', `${(row.balancedAccuracy * 100).toFixed(1)}%`));
    return tr;
  });
  element('intent-rows').replaceChildren(...rows);
} catch { element('intent-status').textContent = 'Intent comparison unavailable or invalid.'; }
