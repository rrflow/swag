import { parseDevStatus } from './dev.js';
const el = (id: string): HTMLElement => { const node = document.getElementById(id); if (!node) throw new Error('Missing UI element'); return node; };
async function refresh() {
  const button = el('refresh') as HTMLButtonElement; button.disabled = true; el('error').hidden = true;
  try {
    const response = await fetch('/api/dev/status', { cache: 'no-store' });
    if (!response.ok) throw new Error('Developer status is unavailable. Check the local API process and traces.');
    const data = parseDevStatus(await response.json());
    el('observed').textContent = `Observed ${new Date(data.observedAt).toLocaleString()}`;
    el('engine').textContent = data.engine.authenticated ? `Authenticated · ${data.engine.instanceId}` : data.engine.state;
    const dataset = data.training.dataset;
    el('dataset').textContent = dataset.counts ? `${dataset.state.replaceAll('_', ' ')} · ${JSON.stringify(dataset.counts)}` :
      dataset.state === 'not_configured' ? 'No reviewed dataset selected' : 'Dataset verification failed';
    el('training').textContent = 'UI job launch unavailable: engine admission is not integrated.';
    const trace = data.observability;
    el('trace-status').textContent = `${trace.files} trace files · ${trace.invalidFiles} invalid · ${trace.incompleteSpans} spans without a terminal outcome`;
    el('timings').replaceChildren();
    for (const row of trace.measurements) {
      const tr = document.createElement('tr');
      for (const value of [row.operation, row.samples, row.errors, row.p50Ms.toFixed(2), row.p95Ms.toFixed(2), row.configurationSha256?.slice(0, 12) ?? 'Not recorded']) {
        const td = document.createElement('td'); td.textContent = String(value); tr.append(td);
      }
      el('timings').append(tr);
    }
    el('failures').replaceChildren();
    if (!trace.recentFailures.length) el('failures').textContent = 'No terminal failures recorded.';
    for (const failure of trace.recentFailures) {
      const p = document.createElement('p');
      p.textContent = `${failure.operation} · ${failure.errorType} · Trace ${failure.traceId}`;
      el('failures').append(p);
    }
    el('runs').replaceChildren();
    if (!data.training.runs.length) el('runs').textContent = data.training.registryState === 'invalid_registry' ? 'Training-run registry could not be read.' : 'No training-run artifacts configured.';
    for (const run of data.training.runs) {
      const article = document.createElement('article'); article.className = 'run';
      const heading = document.createElement('h3'); heading.textContent = run.id; article.append(heading);
      const detail = document.createElement('p');
      detail.textContent = `${run.state.replaceAll('_', ' ')} · ${(run.datasetBasis ?? 'unknown dataset basis').replaceAll('_', ' ')} · ${run.precision ?? 'Precision unknown'}`;
      article.append(detail);
      const identity = document.createElement('p'); identity.className = 'note';
      identity.textContent = `${run.model ?? 'Model unknown'} @ ${run.modelRevision ?? 'Revision unknown'}`; article.append(identity);
      const metrics = document.createElement('dl');
      const labels: Record<string, string> = { gpu_peak_allocated_bytes: 'Peak training memory allocated', gpu_peak_reserved_bytes: 'Peak training memory reserved', train_runtime: 'Training duration', train_loss: 'Training loss' };
      for (const [key, value] of Object.entries(run.metrics)) {
        const term = document.createElement('dt'); term.textContent = labels[key] ?? key;
        const measured = document.createElement('dd');
        measured.textContent = key.endsWith('_bytes') ? `${(value / 2 ** 30).toFixed(2)} GiB` : key === 'train_runtime' ? `${value.toFixed(2)} seconds` : value.toPrecision(5);
        metrics.append(term, measured);
      }
      article.append(metrics); el('runs').append(article);
    }
  } catch (error) {
    el('error').textContent = error instanceof Error ? error.message : 'Unable to read status'; el('error').hidden = false;
  } finally { button.disabled = false; }
}
el('refresh').addEventListener('click', refresh);
void refresh();
