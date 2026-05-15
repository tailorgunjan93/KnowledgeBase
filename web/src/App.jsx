import { useState, useCallback, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthPage, Sidebar, SummarizerPage } from './components';
import { ChatPage, KnowledgeBasePage, SettingsPage, AdminPage } from './pages';
import { chatAPI } from './api';

function AppContent() {
  const { user, loading, login } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [chatResetKey, setChatResetKey] = useState(0);

  const handleNewChat = () => {
    setCurrentSession(null);
    setActiveTab('chat');
    setChatResetKey(k => k + 1); // Force clean slate ONLY on explicit New Chat
  };

  const fetchSessions = useCallback(async () => {
    try {
      const res = await chatAPI.getSessions();
      setSessions(res.data || []);
    } catch { /* silent */ }
  }, []);

  // Initial load
  useEffect(() => {
    const init = async () => {
      try {
        const res = await chatAPI.getSessions();
        const sessionsData = res.data || [];
        setSessions(sessionsData);
        if (sessionsData.length > 0) {
          setCurrentSession(sessionsData[0].id);
        }
      } catch { /* silent */ }
    };
    init();
  }, []);

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
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
      />
      <main className="main-content">
        {activeTab === 'chat' && (
          <ChatPage
            key={chatResetKey}
            currentSession={currentSession}
            setCurrentSession={setCurrentSession}
            onSessionCreated={fetchSessions}
          />
        )}
        {activeTab === 'kb' && <KnowledgeBasePage />}
        {activeTab === 'summarizer' && <SummarizerPage />}
        {activeTab === 'settings' && <SettingsPage user={user} />}
        {activeTab === 'admin' && <AdminPage />}
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
