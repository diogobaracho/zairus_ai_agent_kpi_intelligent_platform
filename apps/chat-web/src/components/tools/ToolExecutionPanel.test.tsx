import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import type { UiMessage } from '../../state/chatReducer';
import { ToolExecutionPanel } from './ToolExecutionPanel';

const message: UiMessage = {
  id: 'a1',
  role: 'assistant',
  content: 'answer',
  status: 'done',
  traceId: 'trace0001abcd',
  usage: { input_tokens: 10, output_tokens: 20, iterations: 3, tool_calls: 2 },
  stoppedReason: 'end_turn',
  steps: [
    {
      id: 's1',
      tool: 'get_kpi_history',
      arguments: { ticker: 'ORBYY', kpi: 'revenue' },
      iteration: 1,
      status: 'error',
      duration_ms: 4,
      result_preview: '{"error":...}',
      error: {
        code: 'company_not_found',
        message: "No company with ticker 'ORBYY'",
        suggestions: [{ value: 'ORBY', label: 'Orbitly Analytics (ORBY)', score: 80 }],
        recovery_hint: 'Retry with ORBY.',
      },
    },
    {
      id: 's2',
      tool: 'get_kpi_history',
      arguments: { ticker: 'ORBY', kpi: 'revenue' },
      iteration: 2,
      status: 'ok',
      duration_ms: 31,
      result_preview: '{"count":16}',
      error: null,
    },
  ],
};

describe('ToolExecutionPanel', () => {
  it('shows each call with arguments, status, duration, error envelope and trace link', async () => {
    render(
      <MemoryRouter>
        <ToolExecutionPanel message={message} />
      </MemoryRouter>,
    );
    expect(screen.getAllByTestId('tool-call-card')).toHaveLength(2);
    expect(screen.getByText('2 calls')).toBeInTheDocument();
    expect(screen.getByText('ticker=ORBYY')).toBeInTheDocument();
    expect(screen.getByText('company_not_found')).toBeInTheDocument();
    expect(screen.getByText('ORBY', { selector: '.chip' })).toBeInTheDocument();
    expect(screen.getByText('Retry with ORBY.')).toBeInTheDocument();
    expect(screen.getByText('31 ms')).toBeInTheDocument();
    expect(screen.getByText('trace trace0001abcd')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /audit/ })).toHaveAttribute(
      'href',
      '/trace/trace0001abcd',
    );
    await userEvent.click(screen.getAllByRole('button', { expanded: false })[1]);
    expect(screen.getByTestId('result-preview')).toHaveTextContent('{"count":16}');
    expect(screen.getByText(/3 iterations · 2 tool calls · 30 tokens/)).toBeInTheDocument();
  });

  it('renders the empty and streaming states', () => {
    const { rerender } = render(
      <MemoryRouter>
        <ToolExecutionPanel message={null} />
      </MemoryRouter>,
    );
    expect(screen.getByText(/Every tool the agent calls/)).toBeInTheDocument();
    rerender(
      <MemoryRouter>
        <ToolExecutionPanel
          message={{ ...message, steps: [], status: 'streaming', usage: undefined }}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText('Thinking…')).toBeInTheDocument();
  });
});
