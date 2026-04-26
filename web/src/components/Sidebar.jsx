import React from 'react';
import { useAuth } from '../context/AuthContext';

export function Sidebar({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>AI Assistant</h2>
        <span className="user-name">{user?.username}</span>
      </div>
      <nav className="sidebar-nav">
        <button
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          <span className="icon">💬</span> Chat
        </button>
        <button
          className={activeTab === 'kb' ? 'active' : ''}
          onClick={() => setActiveTab('kb')}
        >
          <span className="icon">📚</span> Knowledge Base
        </button>
        <button
          className={activeTab === 'summarizer' ? 'active' : ''}
          onClick={() => setActiveTab('summarizer')}
        >
          <span className="icon">📝</span> Summarizer
        </button>
        <button
          className={activeTab === 'settings' ? 'active' : ''}
          onClick={() => setActiveTab('settings')}
        >
          <span className="icon">⚙️</span> Settings
        </button>
      </nav>
      <div className="sidebar-footer">
        <button onClick={logout} className="logout-btn">Logout</button>
      </div>
    </aside>
  );
}