import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthPage, Sidebar, ChatPage, KnowledgeBasePage, SummarizerPage, SettingsPage } from './components';

function AppContent() {
  const { user, loading, login } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!user) {
    return <AuthPage onLogin={login} />;
  }

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {activeTab === 'chat' && <ChatPage user={user} />}
        {activeTab === 'kb' && <KnowledgeBasePage user={user} />}
        {activeTab === 'summarizer' && <SummarizerPage user={user} />}
        {activeTab === 'settings' && <SettingsPage user={user} />}
      </main>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;