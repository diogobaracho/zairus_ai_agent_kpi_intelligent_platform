import { API_BASE, ProblemError } from './client';
import type { Problem, SseEvent } from './types';

/** Parse a chunk buffer of SSE text into complete events; returns the unparsed remainder. */
export function parseSseChunk(buffer: string): { events: SseEvent[]; rest: string } {
  const events: SseEvent[] = [];
  const parts = buffer.split(/\r?\n\r?\n/);
  const rest = parts.pop() ?? '';
  for (const block of parts) {
    let name = '';
    const dataLines: string[] = [];
    for (const line of block.split(/\r?\n/)) {
      if (line.startsWith(':')) continue; // keepalive comment
      if (line.startsWith('event:')) name = line.slice(6).trim();
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
    }
    if (!name || dataLines.length === 0) continue;
    try {
      events.push({ event: name, data: JSON.parse(dataLines.join('\n')) } as SseEvent);
    } catch {
      // ignore malformed frames; the server always sends JSON
    }
  }
  return { events, rest };
}

export type StreamHandler = (event: SseEvent) => void;

/** POST a chat message and dispatch each SSE event; resolves when the stream ends. */
export async function streamChat(
  body: { message: string; conversation_id?: string | null },
  onEvent: StreamHandler,
  signal?: AbortSignal,
  traceId?: string,
): Promise<void> {
  const response = await fetch(`${API_BASE}/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(traceId ? { 'X-Correlation-Id': traceId } : {}),
    },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const text = await response.text();
    let problem: Problem;
    try {
      problem = JSON.parse(text) as Problem;
    } catch {
      problem = {
        title: response.statusText,
        status: response.status,
        detail: text,
        code: 'http_error',
      };
    }
    throw new ProblemError(problem);
  }
  if (!response.body)
    throw new ProblemError({
      title: 'No stream',
      status: 502,
      detail: 'empty response body',
      code: 'no_stream',
    });
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseSseChunk(buffer);
    buffer = rest;
    events.forEach(onEvent);
  }
  const { events } = parseSseChunk(buffer + '\n\n');
  events.forEach(onEvent);
}
