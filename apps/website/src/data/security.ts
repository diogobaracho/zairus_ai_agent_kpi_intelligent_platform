export const boundaries = ['llm', 'data', 'callers'] as const;

export const failureModes = [
  'hallucination',
  'unknownTool',
  'malformed',
  'identity',
  'loop',
  'slow',
  'outage',
] as const;
