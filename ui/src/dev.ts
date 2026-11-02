export type Measurement = { operation: string; samples: number; errors: number; p50Ms: number; p95Ms: number; maxMs: number; configurationSha256: string | null };
export type DevStatus = { schema: 'swag.dev-status/v1'; observedAt: string;
  engine: { state: string; authenticated: boolean; instanceId?: string };
  observability: { files: number; invalidFiles: number; incompleteSpans: number; measurements: Measurement[]; recentFailures: { traceId: string; operation: string; timestamp: string; errorType: string }[] };
  training: { dataset: { state: string; counts: Record<string, number> | null; manifestSha256: string | null }; launchAvailable: false; registryState: string; runs: { id: string; state: string; metrics: Record<string, number>; model?: string | null; modelRevision?: string | null; precision?: string | null; artifactKind?: string | null; baseQuantized?: boolean | null; datasetBasis?: string }[] };
  integration: { connectomeIntegrated: false; subscriptionUsageObserved: false; rroflowTraceExportAvailable: false };
};
export function parseDevStatus(value: unknown): DevStatus {
  if (!value || typeof value !== 'object') throw new Error('Invalid developer status');
  const data = value as DevStatus;
  if (data.schema !== 'swag.dev-status/v1' || !Number.isFinite(Date.parse(data.observedAt)) ||
      typeof data.engine?.authenticated !== 'boolean' || !['not_configured', 'connected', 'unavailable'].includes(data.engine?.state) ||
      (data.engine.authenticated !== (data.engine.state === 'connected')) ||
      data.training?.launchAvailable !== false || !Array.isArray(data.training.runs) ||
      !['not_configured', 'verified_export', 'empty_export', 'invalid_export'].includes(data.training.dataset?.state) ||
      !['not_configured', 'read', 'invalid_registry'].includes(data.training.registryState) || !Array.isArray(data.observability?.measurements) ||
      data.integration?.connectomeIntegrated !== false || data.integration.subscriptionUsageObserved !== false ||
      data.integration.rroflowTraceExportAvailable !== false) throw new Error('Unsupported developer status');
  const nonnegative = (n: unknown): n is number => typeof n === 'number' && Number.isFinite(n) && n >= 0;
  const dataset = data.training.dataset;
  if (['verified_export', 'empty_export'].includes(dataset.state)) {
    if (!dataset.counts || Object.keys(dataset.counts).sort().join() !== 'acceptance,development,train' ||
        !Object.values(dataset.counts).every(n => nonnegative(n) && Number.isInteger(n)) ||
        typeof dataset.manifestSha256 !== 'string' || !/^[a-f0-9]{64}$/.test(dataset.manifestSha256)) throw new Error('Invalid dataset observation');
  } else if (dataset.counts !== null || dataset.manifestSha256 !== null) throw new Error('Unverified dataset observation');
  for (const n of [data.observability.files, data.observability.invalidFiles, data.observability.incompleteSpans]) {
    if (!nonnegative(n) || !Number.isInteger(n)) throw new Error('Invalid trace count');
  }
  for (const row of data.observability.measurements) {
    if (!row || typeof row.operation !== 'string' || ![row.samples, row.errors, row.p50Ms, row.p95Ms, row.maxMs].every(nonnegative) ||
        !Number.isInteger(row.samples) || row.samples < 1 || !Number.isInteger(row.errors) || row.errors > row.samples ||
        row.p50Ms > row.p95Ms || row.p95Ms > row.maxMs ||
        (row.configurationSha256 !== null && !/^[a-f0-9]{64}$/.test(row.configurationSha256))) throw new Error('Invalid timing observation');
  }
  if (!Array.isArray(data.observability.recentFailures)) throw new Error('Invalid failure observations');
  for (const row of data.observability.recentFailures) {
    if (!row || !/^[0-9a-f]{32}$/.test(row.traceId) || typeof row.operation !== 'string' ||
        typeof row.errorType !== 'string' || !Number.isFinite(Date.parse(row.timestamp))) throw new Error('Invalid failure observation');
  }
  for (const run of data.training.runs) {
    if (!run || typeof run.id !== 'string' || !['unavailable', 'invalid_artifact', 'configured_outcome_unknown', 'completion_record_present'].includes(run.state) || !run.metrics || !Object.values(run.metrics).every(nonnegative)) throw new Error('Invalid training observation');
    for (const key of ['model', 'modelRevision', 'precision', 'artifactKind'] as const) {
      if (run[key] != null && typeof run[key] !== 'string') throw new Error('Invalid model identity');
    }
  }
  return data;
}
