# Tool loop runaway

**Symptom**: `agent_run.stopped_reason` is `max_iterations` or `wall_clock`; many
`tool_call_audit` rows for one `trace_id`; `repeated_failing_call` rejections.

**Working as designed?** Yes: the budget stopped the run and the user got an explanation plus
the steps. The interesting question is why the model looped.

**Diagnose**: `GET /v1/audit/tool-calls?trace_id=…`; look for the same error envelope repeated;
check whether `suggestions` were empty (fuzzy cutoff too high) or the hint was unclear.

**Fix**: improve the envelope/hint or alias table (`kpi_core/fuzzy.py`), tune
`KPI_AGENT_MAX_ITERATIONS`, or add a prompt rule. Add the transcript to the eval notes.

**Escalate**: if loops correlate with a provider model change.
