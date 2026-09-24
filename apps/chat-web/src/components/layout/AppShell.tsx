import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquare, Compass } from 'lucide-react';
import { useChat } from '../../state/useChat';
import { brand } from '../../brand';

const link = ({ isActive }: { isActive: boolean }) =>
  `inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium ${isActive ? 'bg-brand-soft text-brand-dark' : 'text-ink-soft hover:bg-slate-100'}`;

export function AppShell({ children }: { children: ReactNode }) {
  const { state } = useChat();
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand text-sm font-bold text-white">
              {brand.initial}
            </span>
            <div>
              <div className="text-sm font-semibold leading-tight">{brand.product}</div>
              <div className="text-xs text-ink-soft">
                {brand.provider} estimates · explainable chat
              </div>
            </div>
          </div>
          <nav className="flex items-center gap-1" aria-label="Main">
            <NavLink to="/chat" className={link}>
              <MessageSquare className="h-4 w-4" /> Chat
            </NavLink>
            <NavLink to="/explore" className={link}>
              <Compass className="h-4 w-4" /> Explorer
            </NavLink>
            {state.provider && (
              <span className="chip ml-2" title="LLM provider / model">
                {state.provider} · {state.model}
              </span>
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">{children}</main>
    </div>
  );
}
