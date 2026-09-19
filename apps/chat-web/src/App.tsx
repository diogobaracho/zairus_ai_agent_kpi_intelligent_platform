import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Spinner } from './components/ui/Spinner';
import { ChatProvider } from './state/ChatProvider';

const ChatPage = lazy(() => import('./components/chat/ChatPage'));
const ExplorePage = lazy(() => import('./components/explore/ExplorePage'));
const CompanyPage = lazy(() => import('./components/explore/CompanyPage'));
const TracePage = lazy(() => import('./components/trace/TracePage'));

export default function App() {
  return (
    <ChatProvider>
      <AppShell>
        <Suspense
          fallback={
            <div className="p-8">
              <Spinner label="Loading…" />
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/explore" element={<ExplorePage />} />
            <Route path="/explore/:ticker" element={<CompanyPage />} />
            <Route path="/trace/:traceId" element={<TracePage />} />
            <Route path="*" element={<Navigate to="/chat" replace />} />
          </Routes>
        </Suspense>
      </AppShell>
    </ChatProvider>
  );
}
