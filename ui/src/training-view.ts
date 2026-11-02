import type { TrainingProgress, TrainingArtifact } from './dev.js';

export function renderTrainingEvidence(parent: HTMLElement, progress?: TrainingProgress, artifact?: TrainingArtifact) {
  if (progress) {
    const status = document.createElement('p');
    status.textContent = progress.globalStep === null ? `Progress: ${progress.state.replaceAll('_', ' ')}` :
      `Recorded step ${progress.globalStep} of ${progress.maxSteps}. Current process liveness is unknown.`;
    if (progress.incompleteTail) status.textContent += ' The latest observation is incomplete.';
    if (progress.lastObservation) status.textContent += ` Last trainer observation: ${progress.lastObservation.replaceAll('_', ' ')}${progress.lastErrorType ? ` (${progress.lastErrorType})` : ''}.`;
    parent.append(status);
    const points = progress.points.filter(row => row.loss !== undefined);
    if (points.length) {
      const figure = document.createElement('figure'); figure.className = 'loss-chart';
      const caption = document.createElement('figcaption');
      caption.textContent = `Recorded training loss · ${points.length} observations. Loss is not routing accuracy.`;
      const ns = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 600 180');
      svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Recorded training loss over optimizer steps');
      const values = points.map(row => row.loss!);
      const low = Math.min(...values), high = Math.max(...values), last = Math.max(...points.map(row => row.step), 1);
      const line = document.createElementNS(ns, 'polyline');
      line.setAttribute('points', points.map(row => `${40 + row.step / last * 540},${145 - ((row.loss! - low) / Math.max(high - low, 1e-12)) * 125}`).join(' '));
      line.setAttribute('fill', 'none'); line.setAttribute('stroke', '#8ee3bb'); line.setAttribute('stroke-width', '2');
      svg.append(line);
      for (const [x, y, value] of [[0, 16, high.toFixed(3)], [0, 149, low.toFixed(3)], [40, 175, 'Step 0'], [530, 175, `Step ${last}`]] as const) {
        const label = document.createElementNS(ns, 'text'); label.setAttribute('x', String(x)); label.setAttribute('y', String(y)); label.setAttribute('fill', '#acb9c0'); label.setAttribute('font-size', '11'); label.textContent = value; svg.append(label);
      }
      const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = 'Inspect recorded loss values'; details.append(summary);
      const table = document.createElement('table');
      const head = document.createElement('tr');
      for (const name of ['Step', 'Training loss']) { const th = document.createElement('th'); th.textContent = name; head.append(th); } table.append(head);
      for (const point of points) {
        const row = document.createElement('tr');
        for (const value of [point.step, point.loss!]) { const td = document.createElement('td'); td.textContent = String(value); row.append(td); } table.append(row);
      }
      details.append(table); figure.append(caption, svg, details); parent.append(figure);
    }
  }
  if (artifact) {
    const p = document.createElement('p'); p.className = 'note';
    p.textContent = artifact.state === 'manifest_recorded' ?
      `Declared weight files: ${(artifact.declaredWeightBytes! / 1e9).toFixed(2)} GB. This is file size, not serving memory. Manifest ${artifact.manifestSha256}.` :
      `Artifact manifest: ${artifact.state.replaceAll('_', ' ')}.`;
    const verification = document.createElement('p'); verification.className = 'note';
    verification.textContent = artifact.verification === 'past_receipt_matches_manifest' ?
      `Recorded byte verification at ${artifact.verifiedAt}. Receipt matches this manifest; weights were not rechecked during this refresh. Model qualification remains unavailable.` :
      `Byte verification: ${artifact.verification.replaceAll('_', ' ')}. No model qualification is claimed.`;
    parent.append(p, verification);
  }
}
