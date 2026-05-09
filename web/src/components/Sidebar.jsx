import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { httpClient } from '../api/httpClient';

export function Sidebar({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();
  const [provider, setProvider] = useState({ active_provider: 'none' });

  useEffect(() => {
    httpClient.get('/api/llm-provider')
      .then(res => setProvider(res.data))
      .catch(() => {});
  }, []);

  const providerLabel = provider.active_provider === 'groq' ? 'Groq Cloud'
    : provider.active_provider === 'ollama' ? 'Ollama Local' : 'No LLM';
  const isOnline = provider.active_provider !== 'none';

  return (
    <aside className="sidebar">
      <div className="sidebar-head">
        <div className="brand">
          <div className="brand-mark">
            <svg viewBox="0 0 26 26" fill="none">
              <path d="M6 4v18" stroke="#0C0B0A" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M6 13L16 5" stroke="#0C0B0A" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M6 13L18 21" stroke="#0C0B0A" strokeWidth="2.5" strokeLinecap="round"/>
              <circle cx="20" cy="5" r="2.5" fill="#0C0B0A" opacity="0.6"/>
            </svg>
          </div>
          <span className="brand-name">KBase</span>
        </div>
        <div className="brand-sub">Knowledge Base AI</div>
      </div>

      <nav className="nav">
        <div className="nav-section-label">Workspace</div>
        <button className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          Chat
        </button>
        <button className={`nav-item ${activeTab === 'kb' ? 'active' : ''}`} onClick={() => setActiveTab('kb')}>
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
          </svg>
          Knowledge Base
        </button>
        <button className={`nav-item ${activeTab === 'summarizer' ? 'active' : ''}`} onClick={() => setActiveTab('summarizer')}>
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          Summarizer
        </button>
        <div className="nav-section-label" style={{marginTop: '8px'}}>System</div>
        <button className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          Settings
        </button>
      </nav>

      <div className="sidebar-foot">
        <div className="llm-status" onClick={() => setActiveTab('settings')}>
          <div className={`status-dot ${isOnline ? 'on' : ''}`}></div>
          <span className="status-text">{providerLabel}</span>
          <span className="status-gear">⚙️</span>
        </div>
        <button className="btn-logout" onClick={logout}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Sign out
        </button>
      </div>
    </aside>
  );
}