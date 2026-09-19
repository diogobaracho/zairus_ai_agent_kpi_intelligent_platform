import { describe, expect, it } from 'vitest';
import type { Step } from '../api/types';
import { chatReducer, initialState } from './chatReducer';

const step = (over: Partial<Step> = {}): Step => ({
  id: 's1',
  tool: 'get_kpi_qtd',
  arguments: { ticker: 'ORBY', kpi: 'revenue' },
  iteration: 1,
  status: 'ok',
  duration_ms: 12,
  result_preview: '{}',
  error: null,
  ...over,
});

describe('chatReducer', () => {
  it('runs through a full streaming turn', () => {
    let s = chatReducer(initialState, {
      type: 'SEND',
      userId: 'u1',
      assistantId: 'a1',
      text: 'hi',
    });
    expect(s.status).toBe('streaming');
    expect(s.messages.map((m) => m.role)).toEqual(['user', 'assistant']);
    s = chatReducer(s, {
      type: 'SESSION',
      assistantId: 'a1',
      session: { conversation_id: 'c1', trace_id: 't1', provider: 'stub', model: 'm' },
    });
    expect(s.conversationId).toBe('c1');
    expect(s.messages[1].traceId).toBe('t1');
    s = chatReducer(s, { type: 'TOOL_STARTED', assistantId: 'a1', step: step({ duration_ms: 0 }) });
    s = chatReducer(s, {
      type: 'TOOL_FINISHED',
      assistantId: 'a1',
      step: step({ duration_ms: 34 }),
    });
    expect(s.messages[1].steps).toHaveLength(1);
    expect(s.messages[1].steps[0].duration_ms).toBe(34);
    s = chatReducer(s, { type: 'TEXT_DELTA', assistantId: 'a1', delta: 'ORBY ' });
    s = chatReducer(s, { type: 'TEXT_DELTA', assistantId: 'a1', delta: 'revenue' });
    expect(s.messages[1].content).toBe('ORBY revenue');
    s = chatReducer(s, {
      type: 'FINAL',
      assistantId: 'a1',
      final: {
        message_id: 'm1',
        answer: 'ORBY revenue is X',
        steps: [step()],
        usage: { input_tokens: 1, output_tokens: 2, iterations: 2, tool_calls: 1 },
        stopped_reason: 'end_turn',
      },
    });
    expect(s.status).toBe('idle');
    expect(s.messages[1]).toMatchObject({
      status: 'done',
      content: 'ORBY revenue is X',
      stoppedReason: 'end_turn',
    });
  });

  it('marks stream and request errors', () => {
    let s = chatReducer(initialState, {
      type: 'SEND',
      userId: 'u1',
      assistantId: 'a1',
      text: 'hi',
    });
    s = chatReducer(s, {
      type: 'STREAM_ERROR',
      assistantId: 'a1',
      code: 'upstream_unavailable',
      message: 'LLM down',
      traceId: 't',
      steps: [step({ status: 'error' })],
    });
    expect(s.status).toBe('error');
    expect(s.messages[1]).toMatchObject({
      status: 'error',
      error: { code: 'upstream_unavailable' },
      traceId: 't',
    });
    expect(s.messages[1].steps[0].status).toBe('error');
    const r = chatReducer(
      chatReducer(initialState, { type: 'SEND', userId: 'u2', assistantId: 'a2', text: 'x' }),
      {
        type: 'REQUEST_ERROR',
        assistantId: 'a2',
        problem: { title: 'Too many', status: 429, detail: 'slow down', code: 'rate_limited' },
      },
    );
    expect(r.error?.code).toBe('rate_limited');
    expect(r.messages[1].content).toBe('slow down');
  });

  it('hydrates and resets', () => {
    const s = chatReducer(initialState, {
      type: 'HYDRATE',
      state: { conversationId: 'c9', messages: [] },
    });
    expect(s.conversationId).toBe('c9');
    expect(chatReducer(s, { type: 'RESET' })).toEqual(initialState);
  });
});
