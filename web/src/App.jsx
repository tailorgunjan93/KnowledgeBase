import { useState, useCallback, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthPage, Sidebar, SummarizerPage } from './components';
import { ChatPage, KnowledgeBasePage, SettingsPage } from './pages';
import { chatAPI } from './api';

function AppContent() {
  const { user, loading, login } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await chatAPI.getSessions();
      const sessionsData = res.data || [];
      setSessions(sessionsData);
      
      // Auto-load latest session if none is active
      if (!currentSession && sessionsData.length > 0) {
        setCurrentSession(sessionsData[0].id);
      }
    } catch { /* silent */ }
  }, [currentSession]);

  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  const handleDeleteSession = useCallback(async (id) => {
    try {
      await chatAPI.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (currentSession === id) setCurrentSession(null);
    } catch { /* silent */ }
  }, [currentSession]);

  if (loading) return <div className="loading-screen" style={{ color: 'var(--color-text)' }}>Loading...</div>;
  if (!user) return <AuthPage onLogin={login} />;

  return (
    <div className="app">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        sessions={sessions}
        currentSession={currentSession}
        onLoadSession={setCurrentSession}
        onNewChat={() => setCurrentSession(null)}
        onDeleteSession={handleDeleteSession}
      />
      <main className="main-content">
        {activeTab === 'chat' && (
          <ChatPage
            currentSession={currentSession}
            setCurrentSession={setCurrentSession}
            onSessionCreated={fetchSessions}
          />
        )}
        {activeTab === 'kb' && <KnowledgeBasePage />}
        {activeTab === 'summarizer' && <SummarizerPage />}
        {activeTab === 'settings' && <SettingsPage user={user} />}
      </main>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
