export type Requirement = {
  id: string; title: string; inputSha256: string; state: 'unassessed' | 'missing_inputs'; fulfillment: 'unassessed';
  decision: { mode: 'choice' | 'score' | 'binary'; question?: string; proposition?: string; rubric?: string;
    options?: { id: string; description: string }[]; minimum?: number; maximum?: number; direction?: string };
  practice: { sha256: string; freshness: 'not_reverified'; question: { id: string; text: string; source: Record<string, unknown> } };
  inputs: Record<string, { path: string; sha256: string | null; bytes: number | null; state: 'read' | 'missing' }[]>;
};
export type KnowledgePreview = { schema: 'swag.knowledge-preview/v1'; state: 'preview' | 'not_configured' | 'unavailable';
  executionAvailable: false; fulfillmentAvailable: false; requirements: Requirement[];
  projectId?: string; templateId?: string; title?: string; templateSha256?: string; projectionSha256?: string };
const hash = (v: unknown): v is string => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const text = (v: unknown): v is string => typeof v === 'string' && v.trim().length > 0;
export function parseKnowledge(value: unknown): KnowledgePreview {
  const data = value as KnowledgePreview;
  if (!data || data.schema !== 'swag.knowledge-preview/v1' ||
      !['preview', 'not_configured', 'unavailable'].includes(data.state) || data.executionAvailable !== false ||
      data.fulfillmentAvailable !== false || !Array.isArray(data.requirements)) throw new Error('Invalid knowledge preview');
  if (data.state !== 'preview') {
    if (data.requirements.length) throw new Error('Unavailable preview cannot expose requirements');
    return data;
  }
  if (!text(data.projectId) || !text(data.templateId) || !text(data.title) || !hash(data.templateSha256) || !hash(data.projectionSha256) ||
      data.requirements.length < 1 || data.requirements.length > 100) throw new Error('Invalid template identity');
  const ids = new Set();
  for (const row of data.requirements) {
    if (!text(row.id) || ids.has(row.id) || !text(row.title) || !hash(row.inputSha256) || row.fulfillment !== 'unassessed' ||
        !['unassessed', 'missing_inputs'].includes(row.state) || !hash(row.practice?.sha256) ||
        row.practice.freshness !== 'not_reverified' || !text(row.practice.question?.id) || !text(row.practice.question.text) ||
        !row.practice.question.source || typeof row.practice.question.source !== 'object' ||
        !row.inputs || typeof row.inputs !== 'object' || Array.isArray(row.inputs)) throw new Error('Invalid requirement');
    ids.add(row.id);
    for (const files of Object.values(row.inputs)) {
      if (!Array.isArray(files)) throw new Error('Invalid input files');
      for (const file of files) {
        if (!text(file.path) || !['read', 'missing'].includes(file.state) ||
            (file.state === 'read' ? !hash(file.sha256) || !Number.isInteger(file.bytes) || file.bytes! < 0 : file.sha256 !== null || file.bytes !== null))
          throw new Error('Invalid file observation');
      }
    }
    const complete = Object.values(row.inputs).length > 0 && Object.values(row.inputs).every(files => files.length && files.every(f => f.state === 'read'));
    if (complete !== (row.state === 'unassessed')) throw new Error('Input readiness mismatch');
    const c = row.decision;
    if (!c || !['choice', 'score', 'binary'].includes(c.mode)) throw new Error('Invalid decision mode');
    if (c.mode === 'binary' && !text(c.proposition)) throw new Error('Missing proposition');
    if (c.mode === 'choice' && (!text(c.question) || !Array.isArray(c.options) || c.options.length < 2 ||
        c.options.some(o => !text(o.id) || !text(o.description)) || new Set(c.options.map(o => o.id)).size !== c.options.length)) throw new Error('Invalid choices');
    if (c.mode === 'score' && (!text(c.rubric) || !Number.isFinite(c.minimum) || !Number.isFinite(c.maximum) || c.minimum! >= c.maximum! ||
        !['higher_is_better', 'lower_is_better'].includes(c.direction!))) throw new Error('Invalid rubric');
  }
  return data;
}

export function changedRequirements(previous: KnowledgePreview | undefined, current: KnowledgePreview): string[] {
  if (!previous || previous.state !== 'preview' || current.state !== 'preview') return [];
  const known = new Map(previous.requirements.map(row => [row.id, row.inputSha256]));
  return current.requirements.filter(row => known.get(row.id) !== row.inputSha256).map(row => row.id);
}
