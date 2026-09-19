import { useCallback, useEffect, useMemo, useReducer, useRef, type ReactNode } from 'react';
import { ProblemError, newTraceId } from '../api/client';
import { getConversation } from '../api/endpoints';
import { streamChat } from '../api/sse';
import type { SseEvent } from '../api/types';
import { chatReducer, initialState, type ChatState, type UiMessage } from './chatReducer';

const STORAGE_KEY = 'zairus.chat.v1';

import { ChatContext } from './context';

export type StreamFn = typeof streamChat;

function loadStored(): Partial<ChatState> | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Partial<ChatState>) : null;
  } catch {
    return null;
  }
}

function persist(state: ChatState): void {
  try {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        conversationId: state.conversationId,
        messages: state.messages.filter((m) => m.status !== 'streaming'),
        provider: state.provider,
        model: state.model,
      }),
    );
  } catch {
    // storage may be unavailable (private mode); the server still holds the conversation
  }
}

export function ChatProvider({
  children,
  stream = streamChat,
}: {
  children: ReactNode;
  stream?: StreamFn;
}) {
  const [state, dispatch] = useReducer(chatReducer, initialState, (init) => {
    const stored = loadStored();
    return stored ? { ...init, ...stored, messages: stored.messages ?? [] } : init;
  });
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    persist(state);
  }, [state]);

  // Rehydrate steps from the server when only the id survived (e.g. storage cleared mid-session).
  useEffect(() => {
    if (state.conversationId && state.messages.length === 0) {
      getConversation(state.conversationId)
        .then((conv) => {
          const messages: UiMessage[] = conv.messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            steps: m.steps,
            status: 'done',
            traceId: m.trace_id,
            stoppedReason: m.stopped_reason ?? undefined,
          }));
          dispatch({ type: 'HYDRATE', state: { messages } });
        })
        .catch(() => dispatch({ type: 'RESET' }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = useCallback(
    async (text: string) => {
      const userId = `u_${newTraceId()}`;
      const assistantId = `a_${newTraceId()}`;
      dispatch({ type: 'SEND', userId, assistantId, text });
      const controller = new AbortController();
      abortRef.current = controller;
      const onEvent = (event: SseEvent) => {
        switch (event.event) {
          case 'session':
            dispatch({ type: 'SESSION', assistantId, session: event.data });
            break;
          case 'text_delta':
            dispatch({ type: 'TEXT_DELTA', assistantId, delta: event.data.delta });
            break;
          case 'tool_call_started':
            dispatch({
              type: 'TOOL_STARTED',
              assistantId,
              step: {
                ...event.data,
                status: 'ok',
                duration_ms: 0,
                result_preview: '',
                error: null,
              },
            });
            break;
          case 'tool_call_finished':
            dispatch({ type: 'TOOL_FINISHED', assistantId, step: event.data });
            break;
          case 'final':
            dispatch({ type: 'FINAL', assistantId, final: event.data });
            break;
          case 'error':
            dispatch({
              type: 'STREAM_ERROR',
              assistantId,
              code: event.data.code,
              message: event.data.message,
              traceId: event.data.trace_id,
              steps: event.data.steps,
            });
            break;
        }
      };
      try {
        await stream(
          { message: text, conversation_id: state.conversationId },
          onEvent,
          controller.signal,
          newTraceId(),
        );
      } catch (error) {
        if (controller.signal.aborted) {
          dispatch({ type: 'STREAM_ERROR', assistantId, code: 'cancelled', message: 'Stopped.' });
        } else if (error instanceof ProblemError) {
          dispatch({ type: 'REQUEST_ERROR', assistantId, problem: error.problem });
        } else {
          dispatch({
            type: 'STREAM_ERROR',
            assistantId,
            code: 'network_error',
            message: 'Connection lost. Please retry.',
          });
        }
      } finally {
        abortRef.current = null;
      }
    },
    [state.conversationId, stream],
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);
  const reset = useCallback(() => {
    abortRef.current?.abort();
    dispatch({ type: 'RESET' });
  }, []);

  const value = useMemo(() => ({ state, send, stop, reset }), [state, send, stop, reset]);
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}
