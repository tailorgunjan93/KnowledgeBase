import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthPage, Sidebar, SummarizerPage } from './components';
import { ChatPage, KnowledgeBasePage, SettingsPage } from './pages';

function AppContent() {
  const { user, loading, login } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');

  if (loading) {
    return <div className="loading-screen" style={{color: 'var(--color-text)'}}>Loading...</div>;
  }

  if (!user) {
    return <AuthPage onLogin={login} />;
  }

  return (
    <div className="app">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
      />
      <main className="main-content">
        {activeTab === 'chat' && <ChatPage />}
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