import type { FinalData, Problem, SessionData, Step } from '../api/types';

export interface UiMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  steps: Step[];
  status: 'streaming' | 'done' | 'error';
  traceId?: string;
  usage?: FinalData['usage'];
  stoppedReason?: string;
  error?: { code: string; message: string } | null;
}

export interface ChatState {
  conversationId: string | null;
  provider: string | null;
  model: string | null;
  messages: UiMessage[];
  status: 'idle' | 'streaming' | 'error';
  error: Problem | null;
}

export type ChatAction =
  | { type: 'SEND'; userId: string; assistantId: string; text: string }
  | { type: 'SESSION'; assistantId: string; session: SessionData }
  | { type: 'TEXT_DELTA'; assistantId: string; delta: string }
  | { type: 'TOOL_STARTED'; assistantId: string; step: Step }
  | { type: 'TOOL_FINISHED'; assistantId: string; step: Step }
  | { type: 'FINAL'; assistantId: string; final: FinalData }
  | {
      type: 'STREAM_ERROR';
      assistantId: string;
      code: string;
      message: string;
      traceId?: string;
      steps?: Step[];
    }
  | { type: 'REQUEST_ERROR'; assistantId: string; problem: Problem }
  | { type: 'HYDRATE'; state: Partial<ChatState> }
  | { type: 'RESET' };

export const initialState: ChatState = {
  conversationId: null,
  provider: null,
  model: null,
  messages: [],
  status: 'idle',
  error: null,
};

function updateMessage(
  state: ChatState,
  id: string,
  patch: (m: UiMessage) => UiMessage,
): ChatState {
  return { ...state, messages: state.messages.map((m) => (m.id === id ? patch(m) : m)) };
}

function upsertStep(steps: Step[], step: Step): Step[] {
  const index = steps.findIndex((s) => s.id === step.id);
  if (index === -1) return [...steps, step];
  const next = steps.slice();
  next[index] = { ...steps[index], ...step };
  return next;
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SEND':
      return {
        ...state,
        status: 'streaming',
        error: null,
        messages: [
          ...state.messages,
          { id: action.userId, role: 'user', content: action.text, steps: [], status: 'done' },
          {
            id: action.assistantId,
            role: 'assistant',
            content: '',
            steps: [],
            status: 'streaming',
          },
        ],
      };
    case 'SESSION':
      return updateMessage(
        {
          ...state,
          conversationId: action.session.conversation_id,
          provider: action.session.provider,
          model: action.session.model,
        },
        action.assistantId,
        (m) => ({ ...m, traceId: action.session.trace_id }),
      );
    case 'TEXT_DELTA':
      return updateMessage(state, action.assistantId, (m) => ({
        ...m,
        content: m.content + action.delta,
      }));
    case 'TOOL_STARTED':
      return updateMessage(state, action.assistantId, (m) => ({
        ...m,
        steps: upsertStep(m.steps, { ...action.step, status: action.step.status ?? 'ok' }),
      }));
    case 'TOOL_FINISHED':
      return updateMessage(state, action.assistantId, (m) => ({
        ...m,
        steps: upsertStep(m.steps, action.step),
      }));
    case 'FINAL':
      return updateMessage({ ...state, status: 'idle' }, action.assistantId, (m) => ({
        ...m,
        content: action.final.answer,
        steps: action.final.steps,
        status: 'done',
        usage: action.final.usage,
        stoppedReason: action.final.stopped_reason,
      }));
    case 'STREAM_ERROR':
      return updateMessage({ ...state, status: 'error' }, action.assistantId, (m) => ({
        ...m,
        status: 'error',
        steps: action.steps?.length ? action.steps : m.steps,
        traceId: action.traceId ?? m.traceId,
        error: { code: action.code, message: action.message },
        content: m.content || action.message,
      }));
    case 'REQUEST_ERROR':
      return {
        ...updateMessage(state, action.assistantId, (m) => ({
          ...m,
          status: 'error',
          error: { code: action.problem.code, message: action.problem.detail },
          content: action.problem.detail,
        })),
        status: 'error',
        error: action.problem,
      };
    case 'HYDRATE':
      return { ...state, ...action.state, status: 'idle', error: null };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}
