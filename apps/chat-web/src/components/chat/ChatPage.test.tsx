import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import type { SseEvent } from '../../api/types';
import { ChatProvider, type StreamFn } from '../../state/ChatProvider';
import ChatPage from './ChatPage';

function fakeStream(events: SseEvent[]): StreamFn {
  return async (_body, onEvent) => {
    for (const e of events) {
      await Promise.resolve();
      onEvent(e);
    }
  };
}

const happy: SseEvent[] = [
  {
    event: 'session',
    data: { conversation_id: 'c1', trace_id: 'tr0000000001', provider: 'stub', model: 'stub-1' },
  },
  {
    event: 'tool_call_started',
    data: {
      id: 's1',
      tool: 'get_kpi_qtd',
      arguments: { ticker: 'ORBY', kpi: 'total_revenue' },
      iteration: 1,
    },
  },
  {
    event: 'tool_call_finished',
    data: {
      id: 's1',
      tool: 'get_kpi_qtd',
      arguments: { ticker: 'ORBY', kpi: 'total_revenue' },
      iteration: 1,
      status: 'ok',
      duration_ms: 20,
      result_preview: '{"latest":...}',
      error: null,
    },
  },
  { event: 'text_delta', data: { delta: 'ORBY revenue QTD as of 2026-09-15: $627.45MM' } },
  {
    event: 'final',
    data: {
      message_id: 'm1',
      answer: 'ORBY revenue QTD as of 2026-09-15: $627.45MM',
      steps: [
        {
          id: 's1',
          tool: 'get_kpi_qtd',
          arguments: { ticker: 'ORBY', kpi: 'total_revenue' },
          iteration: 1,
          status: 'ok',
          duration_ms: 20,
          result_preview: '{"latest":...}',
          error: null,
        },
      ],
      usage: { input_tokens: 1, output_tokens: 1, iterations: 2, tool_calls: 1 },
      stopped_reason: 'end_turn',
    },
  },
];

function renderPage(stream: StreamFn) {
  return render(
    <MemoryRouter>
      <ChatProvider stream={stream}>
        <ChatPage />
      </ChatProvider>
    </MemoryRouter>,
  );
}

describe('ChatPage', () => {
  it('streams an answer and shows the tool call with arguments', async () => {
    const stream = vi.fn(fakeStream(happy));
    renderPage(stream);
    await userEvent.type(
      screen.getByLabelText('Ask a question'),
      'What is ORBY total revenue QTD?{enter}',
    );
    await waitFor(() =>
      expect(screen.getByText(/ORBY revenue QTD as of 2026-09-15/)).toBeInTheDocument(),
    );
    expect(stream).toHaveBeenCalledWith(
      expect.objectContaining({ message: 'What is ORBY total revenue QTD?' }),
      expect.any(Function),
      expect.any(AbortSignal),
      expect.any(String),
    );
    expect(
      screen.getByText('get_kpi_qtd', { selector: '.font-mono.font-semibold' }),
    ).toBeInTheDocument();
    expect(screen.getByText('ticker=ORBY')).toBeInTheDocument();
    expect(screen.getByText('trace tr0000000001')).toBeInTheDocument();
    expect(JSON.parse(sessionStorage.getItem('zairus.chat.v1') ?? '{}').conversationId).toBe('c1');
  });

  it('shows an error banner with code and trace id when the request is rejected', async () => {
    const { ProblemError } = await import('../../api/client');
    const stream: StreamFn = async () => {
      throw new ProblemError({
        title: 'Too many requests',
        status: 429,
        detail: 'Too many requests from this client',
        code: 'rate_limited',
        trace_id: 'tr429',
        recovery_hint: 'Retry after 1 seconds.',
      });
    };
    renderPage(stream);
    await userEvent.click(screen.getByText("What's ORBY's QTD total revenue this quarter?"));
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByRole('alert')).toHaveTextContent('rate_limited');
    expect(screen.getByRole('alert')).toHaveTextContent('trace tr429');
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('surfaces a stream error event with its partial steps', async () => {
    const events: SseEvent[] = [
      happy[0],
      {
        event: 'error',
        data: {
          code: 'upstream_unavailable',
          message: 'LLM down',
          trace_id: 'tr0000000001',
          steps: [],
        },
      },
    ];
    renderPage(fakeStream(events));
    await userEvent.type(screen.getByLabelText('Ask a question'), 'hi{enter}');
    await waitFor(() => expect(screen.getByText('LLM down')).toBeInTheDocument());
    expect(screen.getByText('upstream_unavailable')).toBeInTheDocument();
  });
});
