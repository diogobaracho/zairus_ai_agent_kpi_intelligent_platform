export const boundaries = [
  {
    title: 'LLM ↔ tools',
    text: 'The model receives tool schemas and tool results only. Arguments it produces are sanitised twice: in the agent and in the MCP server.',
  },
  {
    title: 'Tools ↔ data',
    text: 'Tools call one domain layer that uses parameterised ORM queries. A CI gate fails the build if raw SQL appears outside migrations.',
  },
  {
    title: 'Callers ↔ services',
    text: 'Per-client rate limits, request body caps, CORS allowlists, health checks and non-root containers.',
  },
];

export const failureModes = [
  {
    mode: 'Hallucinated ticker or misspelled KPI',
    guard: 'Error envelope with suggestions and a recovery hint; the prompt allows one retry.',
  },
  {
    mode: 'Unknown tool name',
    guard: 'Rejected in the agent before any network call; the model is told which tools exist.',
  },
  {
    mode: 'Malformed or truncated tool input',
    guard: 'Never executed; recorded as a rejected step.',
  },
  {
    mode: 'Identity smuggling (tenant_id in arguments)',
    guard: 'No such parameter exists; unknown keys are dropped and counted.',
  },
  {
    mode: 'Infinite retry loop',
    guard: 'Iteration budget, duplicate-failing-call ledger and a wall-clock limit.',
  },
  {
    mode: 'Slow or huge tool results',
    guard: 'Per-call timeouts and result truncation with a note to the model.',
  },
  {
    mode: 'Model refusal or provider outage',
    guard: 'Explained to the user; partial steps are persisted with the trace id.',
  },
];
