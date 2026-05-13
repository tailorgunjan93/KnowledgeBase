import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { httpClient } from '../api/httpClient';
import { chatAPI } from '../api';

export function Sidebar({ activeTab, setActiveTab, sessions, currentSession, onLoadSession, onNewChat, onDeleteSession }) {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [provider, setProvider] = useState({ active_provider: 'none' });
  const [collapsed, setCollapsed] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    httpClient.get('/api/llm-provider').then(res => setProvider(res.data)).catch(() => {});
  }, []);

  // Fetch sessions when chat tab is active
  useEffect(() => {
    if (activeTab === 'chat') {
      chatAPI.getSessions().then(res => {
        // sessions are managed by App, but we trigger a refresh via onNewChat side-effect
      }).catch(() => {});
    }
  }, [activeTab]);

  const providerLabel =
    provider.active_provider === 'groq'   ? 'Groq Cloud' :
    provider.active_provider === 'openai' ? 'OpenAI' :
    provider.active_provider === 'gemini' ? 'Google Gemini' :
    provider.active_provider === 'nvidia' ? 'NVIDIA NIM' :
    provider.active_provider === 'aws'    ? 'AWS Bedrock' :
    provider.active_provider === 'ollama' ? 'Ollama Local' : 'No LLM';
  const isOnline = provider.active_provider !== 'none';
  const isDark = theme === 'dark';

  const filteredSessions = sessions.filter(s =>
    (s.title || '').toLowerCase().includes(search.toLowerCase())
  );

  const fmt = (d) => new Date(d || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const NavItem = ({ tab, icon, label }) => (
    <button
      className={`nav-item ${activeTab === tab ? 'active' : ''}`}
      onClick={() => setActiveTab(tab)}
      title={collapsed ? label : undefined}
    >
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        {icon}
      </svg>
      {!collapsed && label}
    </button>
  );

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Header */}
      <div className="sidebar-head">
        {!collapsed && (
          <div className="brand">
            <div className="brand-mark">
              <svg viewBox="0 0 26 26" fill="none">
                <path d="M6 4v18" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
                <path d="M6 13L16 5" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
                <path d="M6 13L18 21" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
                <circle cx="20" cy="5" r="2.5" fill="rgba(255,255,255,0.7)"/>
              </svg>
            </div>
            <div>
              <div className="brand-name">KBase</div>
              <div className="brand-sub">Knowledge Base AI</div>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="brand-mark" style={{ margin: '0 auto' }}>
            <svg viewBox="0 0 26 26" fill="none">
              <path d="M6 4v18" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M6 13L16 5" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M6 13L18 21" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
              <circle cx="20" cy="5" r="2.5" fill="rgba(255,255,255,0.7)"/>
            </svg>
          </div>
        )}
        <button className="sidebar-collapse-btn" onClick={() => setCollapsed(p => !p)} title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            {collapsed
              ? <><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></>
              : <><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></>
            }
          </svg>
        </button>
      </div>

      <div className="nav" style={{ overflowY: 'auto', flex: 1 }}>
        {/* New Chat button */}
        {activeTab === 'chat' && (
          <button className="btn-new" onClick={onNewChat} title={collapsed ? 'New Chat' : undefined}
            style={collapsed ? { padding: 'var(--space-2)', justifyContent: 'center' } : {}}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            {!collapsed && 'New Chat'}
          </button>
        )}

        {!collapsed && <div className="nav-section-label">Workspace</div>}

        <NavItem tab="chat" label="Chat" icon={<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>} />
        <NavItem tab="kb" label="Knowledge Base" icon={<><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></>} />

        {!collapsed && <div className="nav-section-label" style={{ marginTop: 'var(--space-3)' }}>System</div>}

        <NavItem tab="settings" label="Settings" icon={<><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></>} />

        {/* Chat history section */}
        {activeTab === 'chat' && !collapsed && (
          <div className="history-section">
            <button className="history-section-header" onClick={() => setHistoryOpen(p => !p)}>
              <span className="nav-section-label" style={{ margin: 0 }}>History</span>
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
                style={{ transform: historyOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', flexShrink: 0 }}>
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>

            {historyOpen && (
              <>
                <div className="search-wrap" style={{ margin: '4px 0 6px' }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  <input className="search-input" style={{ fontSize: '12px' }} type="text"
                    placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)} />
                </div>

                <div className="threads-list" style={{ maxHeight: '40vh', overflowY: 'auto', padding: 0 }}>
                  {filteredSessions.length === 0 && (
                    <div style={{ padding: '8px 4px', fontSize: 'var(--text-xs)', color: 'var(--color-text-faint)' }}>
                      No conversations yet.
                    </div>
                  )}
                  {filteredSessions.map(s => (
                    <div
                      key={s.id}
                      className={`thread-item ${currentSession === s.id ? 'active' : ''}`}
                      onClick={() => onLoadSession(s.id)}
                      style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '8px 6px' }}
                    >
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div className="thread-title">{s.title || `Chat ${s.id}`}</div>
                        <div className="thread-meta">{s.created_at ? fmt(s.created_at) : 'Recent'}</div>
                      </div>
                      <button
                        className="thread-del-btn"
                        title="Delete chat"
                        onClick={e => { e.stopPropagation(); onDeleteSession(s.id); }}
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3 6 5 6 21 6"/>
                          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                          <path d="M10 11v6M14 11v6"/>
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Collapsed history icon */}
        {activeTab === 'chat' && collapsed && (
          <button className="nav-item" title="History" style={{ justifyContent: 'center' }}>
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </button>
        )}
      </div>

      {/* Footer */}
      <div className="sidebar-foot">
        <div className="theme-toggle-sidebar" onClick={toggleTheme} title={collapsed ? (isDark ? 'Light mode' : 'Dark mode') : undefined}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="2">
            {isDark
              ? <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              : <><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></>
            }
          </svg>
          {!collapsed && <span className="theme-toggle-label">{isDark ? 'Dark mode' : 'Light mode'}</span>}
          {!collapsed && (
            <button className={`theme-pill ${isDark ? 'dark' : ''}`} onClick={e => { e.stopPropagation(); toggleTheme(); }}>
              <div className="theme-pill-thumb" />
            </button>
          )}
        </div>

        <div className="llm-status" onClick={() => setActiveTab('settings')} title={collapsed ? providerLabel : undefined}
          style={collapsed ? { justifyContent: 'center', padding: 'var(--space-2)' } : {}}>
          <div className={`status-dot ${isOnline ? 'on' : ''}`} />
          {!collapsed && <span className="status-text">{providerLabel}</span>}
          {!collapsed && <span className="status-gear">⚙️</span>}
        </div>

        <button className="btn-logout" onClick={logout} title={collapsed ? 'Sign out' : undefined}
          style={collapsed ? { justifyContent: 'center' } : {}}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          {!collapsed && 'Sign out'}
        </button>
      </div>
    </aside>
  );
}
