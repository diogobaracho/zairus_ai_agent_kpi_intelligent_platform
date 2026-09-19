import { describe, expect, it } from 'vitest';
import { parseSseChunk } from './sse';

describe('parseSseChunk', () => {
  it('parses complete events and keeps the remainder', () => {
    const text =
      'id: 1\r\nevent: session\r\ndata: {"conversation_id":"c","trace_id":"t","provider":"stub","model":"m"}\r\n\r\n: keepalive\r\n\r\nevent: text_delta\r\ndata: {"delta":"hi"}\r\n\r\nevent: final\r\ndata: {"ans';
    const { events, rest } = parseSseChunk(text);
    expect(events.map((e) => e.event)).toEqual(['session', 'text_delta']);
    expect(events[0].data).toMatchObject({ conversation_id: 'c', trace_id: 't' });
    expect(rest).toBe('event: final\r\ndata: {"ans');
  });

  it('handles LF-only frames and multi-line data', () => {
    const { events } = parseSseChunk('event: text_delta\ndata: {"delta":\ndata: "x"}\n\n');
    expect(events[0]).toEqual({ event: 'text_delta', data: { delta: 'x' } });
  });

  it('ignores malformed frames', () => {
    const { events } = parseSseChunk('event: final\ndata: not json\n\n');
    expect(events).toEqual([]);
  });
});
