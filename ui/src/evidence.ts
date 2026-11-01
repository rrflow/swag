export type CaseEvidence = {
  caseRef: string; validOutput: boolean; matched: boolean; policyViolation: boolean;
  falseAbstention: boolean; unnecessarySelection: boolean; elapsedSeconds: number;
};
export type Evidence = {
  schemaVersion: 1; kind: 'swag.offline_evidence'; runId: string; completedAt: string;
  scope: 'development' | 'acceptance';
  model: { name: string; precision: string; customCheckpoint: boolean };
  provenance: { protocolSha256: string; resultsSha256: string; artifactManifestSha256: string };
  metrics: { cases: number; matched: number; accuracy: number; policyViolations: number;
    invalidOutputs: number; falseAbstentions: number; unnecessarySelections: number;
    firstRequestSeconds: number; warmMedianSeconds: number | null; p95Seconds: number;
    protocolPassed: boolean; deploymentQualified: false };
  cases: CaseEvidence[];
  signals: { signal: string; rule_version: number; severity: string; summary: string; score: number }[];
  learningSuggestions: { kind: string; state: string; reason: string }[];
  authority: { engineReceipt: null; trainingAuthorized: false; promotionAuthorized: false;
    connectomeIntegrated: false; rroflowAccepted: false };
};

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Expected an object');
  return value as Record<string, unknown>;
}
function string(value: unknown): asserts value is string {
  if (typeof value !== 'string' || !value || value.length > 1000) throw new Error('Invalid text field');
}
function boolean(value: unknown): asserts value is boolean {
  if (typeof value !== 'boolean') throw new Error('Invalid boolean field');
}
function number(value: unknown): asserts value is number {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) throw new Error('Invalid metric');
}

export function parseEvidence(value: unknown): Evidence {
  const data = object(value);
  if (data.schemaVersion !== 1 || data.kind !== 'swag.offline_evidence' ||
      !['development', 'acceptance'].includes(String(data.scope))) throw new Error('Unsupported evidence format');
  string(data.runId); string(data.completedAt);
  if (!/^[a-f0-9]{64}$/.test(data.runId) || Number.isNaN(Date.parse(data.completedAt))) throw new Error('Invalid run identity');
  const model = object(data.model);
  string(model.name); string(model.precision); boolean(model.customCheckpoint);
  for (const key of ['protocolSha256', 'resultsSha256', 'artifactManifestSha256']) {
    const hash = object(data.provenance)[key];
    if (typeof hash !== 'string' || !/^[a-f0-9]{64}$/.test(hash)) throw new Error('Missing evidence digest');
  }
  const authority = object(data.authority);
  if (authority.engineReceipt !== null || ['trainingAuthorized', 'promotionAuthorized', 'connectomeIntegrated', 'rroflowAccepted']
      .some(key => authority[key] !== false)) throw new Error('This viewer accepts offline evidence only');
  const metrics = object(data.metrics);
  for (const key of ['cases', 'matched', 'policyViolations', 'invalidOutputs', 'falseAbstentions', 'unnecessarySelections']) {
    number(metrics[key]);
    if (!Number.isInteger(metrics[key])) throw new Error('Counts must be integers');
  }
  for (const key of ['accuracy', 'firstRequestSeconds', 'p95Seconds']) number(metrics[key]);
  if (metrics.warmMedianSeconds !== null) number(metrics.warmMedianSeconds);
  boolean(metrics.protocolPassed);
  if (metrics.deploymentQualified !== false) throw new Error('Offline evidence cannot qualify deployment');
  if (!Array.isArray(data.cases) || data.cases.length < 1 || data.cases.length > 10000) throw new Error('Invalid cases');
  const ids = new Set();
  for (const row of data.cases) {
    const item = object(row); string(item.caseRef); number(item.elapsedSeconds);
    if (!/^[a-f0-9]{16}$/.test(item.caseRef) || ids.has(item.caseRef)) throw new Error('Invalid case identity');
    ids.add(item.caseRef);
    for (const key of ['validOutput', 'matched', 'policyViolation', 'falseAbstention', 'unnecessarySelection']) boolean(item[key]);
    if (item.matched && (!item.validOutput || item.policyViolation || item.falseAbstention || item.unnecessarySelection)) throw new Error('Contradictory case result');
  }
  const cases = data.cases as CaseEvidence[];
  const counts = { cases: cases.length, matched: cases.filter(row => row.matched).length,
    policyViolations: cases.filter(row => row.policyViolation).length,
    invalidOutputs: cases.filter(row => !row.validOutput).length,
    falseAbstentions: cases.filter(row => row.falseAbstention).length,
    unnecessarySelections: cases.filter(row => row.unnecessarySelection).length };
  if (Object.entries(counts).some(([key, count]) => metrics[key] !== count) ||
      Math.abs(Number(metrics.accuracy) - counts.matched / counts.cases) > 1e-10) throw new Error('Metrics disagree with cases');
  for (const key of ['signals', 'learningSuggestions']) {
    if (!Array.isArray(data[key]) || data[key].length > 100) throw new Error('Invalid signals');
  }
  for (const row of data.signals as unknown[]) {
    const signal = object(row); string(signal.signal); string(signal.summary);
    string(signal.severity); number(signal.score); number(signal.rule_version);
  }
  for (const row of data.learningSuggestions as unknown[]) {
    const suggestion = object(row); string(suggestion.kind); string(suggestion.state); string(suggestion.reason);
  }
  return data as unknown as Evidence;
}

export function outcome(row: CaseEvidence): string {
  if (!row.validOutput) return 'Invalid output';
  if (row.policyViolation) return 'Policy violation';
  if (row.falseAbstention) return 'False abstention';
  return row.matched ? 'Matched' : 'Different choice';
}
