export type Spread = { samples: number; median: number; p95: number };
export type QuestionRecord = {
  mode: 'binary' | 'choice' | 'score'; status: 'answered' | 'abstained' | 'required' | 'defaulted';
  value?: unknown; option?: string; confidence?: number; probability?: number; abstainBelow?: number; abstainBelowOrigin?: string;
  reason?: string; abstainReason?: string; rules: string[]; skippedRules: { rule: string; reason: string; fact?: string }[];
  preferences: { key: string; value: unknown; layer?: string; reason?: string }[]; forbidden?: string[]; defaultedBy?: string;
  engineMs?: number; instructions: string; answer?: Record<string, unknown>;
};
export type DecisionRecord = {
  schema: 'swag.decision-log/v1'; id: string; at: string; source: string; template: string | null;
  stateSha256: string; stateChars: number; engine: { consulted: boolean; model?: string; protocol?: string; rotations?: boolean };
  timings: Record<string, number>; effectiveDigest: string; staleFacts: string[]; ruleConflicts: unknown[];
  suggestions: { question: string; when: string; text: string; status: string; byRule: boolean }[];
  questions: Record<string, QuestionRecord>;
};
export type DecisionLog = {
  schema: 'swag.decision-log/v1'; state: 'recorded' | 'empty'; requests: number;
  byMode: Record<string, Record<string, number>>; hopsMs: Record<string, Spread>; confidence: Record<string, Spread>;
  records: DecisionRecord[];
};

const MODES = ['binary', 'choice', 'score'];
const STATUSES = ['answered', 'abstained', 'required', 'defaulted'];
const hash = (v: unknown): v is string => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const finite = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const spread = (v: Spread) => v && Number.isInteger(v.samples) && finite(v.median) && finite(v.p95);

export function parseDecisionLog(value: unknown): DecisionLog {
  const data = value as DecisionLog;
  if (!data || data.schema !== 'swag.decision-log/v1' || !['recorded', 'empty'].includes(data.state) ||
      !Number.isInteger(data.requests) || !Array.isArray(data.records) || typeof data.byMode !== 'object' ||
      typeof data.hopsMs !== 'object' || typeof data.confidence !== 'object') throw new Error('Invalid decision log');
  if (Object.values(data.hopsMs).some(v => !spread(v)) || Object.values(data.confidence).some(v => !spread(v))) throw new Error('Invalid timing summary');
  for (const record of data.records) {
    if (record.schema !== 'swag.decision-log/v1' || typeof record.id !== 'string' || Number.isNaN(Date.parse(record.at)) ||
        !hash(record.stateSha256) || !hash(record.effectiveDigest) || !record.questions || typeof record.questions !== 'object' ||
        !Array.isArray(record.suggestions) || typeof record.engine?.consulted !== 'boolean') throw new Error('Invalid decision record');
    for (const question of Object.values(record.questions)) {
      if (!MODES.includes(question.mode) || !STATUSES.includes(question.status) || !Array.isArray(question.rules) ||
          !Array.isArray(question.preferences) || (question.confidence !== undefined && !finite(question.confidence)))
        throw new Error('Invalid question decision');
      if (question.status === 'answered' && question.value === undefined) throw new Error('Answered decision without a value');
      if (question.status === 'abstained' && question.value !== null) throw new Error('Abstention with a value');
    }
  }
  return data;
}

/** One line for a question's decision, saying who decided: the model, a rule or nobody. */
export function describe(question: QuestionRecord): string {
  const value = question.value === null || question.value === undefined ? '' : ` ${JSON.stringify(question.value)}`;
  const confidence = question.confidence === undefined ? '' : ` · confidence ${question.confidence.toFixed(2)}`;
  const floor = question.abstainBelow ? ` (floor ${question.abstainBelow.toFixed(2)} from ${question.abstainBelowOrigin ?? 'default'})` : '';
  switch (question.status) {
    case 'answered': return `Model answered${value}${confidence}${floor}`;
    case 'required': return `Hard rule ${question.rules.join(', ')} set${value}; model not asked`;
    case 'defaulted': return `Abstained (${(question.abstainReason ?? 'unknown').replaceAll('_', ' ')}); rule ${question.defaultedBy} set${value}`;
    default: return `Abstained: ${(question.reason ?? 'unknown').replaceAll('_', ' ')}${confidence}${floor}`;
  }
}
