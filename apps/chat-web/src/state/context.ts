import { createContext } from 'react';
import type { ChatState } from './chatReducer';

export interface ChatContextValue {
  state: ChatState;
  send: (text: string) => Promise<void>;
  stop: () => void;
  reset: () => void;
}

export const ChatContext = createContext<ChatContextValue | null>(null);
