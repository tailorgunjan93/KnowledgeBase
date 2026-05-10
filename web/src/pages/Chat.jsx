import { useState, useEffect, useRef } from 'react';
import { useRAGQuery } from '../hooks/useRAGQuery';
import { useDocuments } from '../hooks/useDocuments';
import { chatAPI } from '../api';
import ConfidenceBadge from '../components/ConfidenceBadge';
import TypingIndicator from '../components/TypingIndicator';

export function ChatPage() {
  const [message,         setMessage]         = useState('');
  const [sessions,        setSessions]        = useState([]);
  const [currentSession,  setCurrentSession]  = useState(null);
  const [messages,        setMessages]        = useState([]);
  const [selectedKBs,     setSelectedKBs]     = useState([]);
  const [useWebSearch,    setUseWebSearch]     = useState(false);
  const [kbDropdownOpen,  setKbDropdownOpen]  = useState(false);
  const [expandedSources, setExpandedSources] = useState({});

  const { query: runQuery, loading, error: queryError } = useRAGQuery();
  const { knowledgeBases, loading: kbsLoading } = useDocuments();

  const endRef   = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { fetchSessions(); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  // Close KB dropdown on outside click
  useEffect(() => {
    const close = () => setKbDropdownOpen(false);
    if (kbDropdownOpen) document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [kbDropdownOpen]);

  const fetchSessions = async () => {
    try {
      const res = await chatAPI.getSessions();
      setSessions(res.data || []);
    } catch { /* silent */ }
  };

  const loadSession = async (sessionId) => {
    try {
      const res = await chatAPI.getMessages(sessionId);
      setMessages(res.data || []);
      setCurrentSession(sessionId);
    } catch { /* silent */ }
  };

  const handleSend = async () => {
    if (!message.trim() || loading) return;
    const userMsg = message;
    setMessage('');
    if (inputRef.current) inputRef.current.style.height = 'auto';

    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);

    try {
      const data = await runQuery(userMsg, {
        session_id: currentSession,
        kb_ids: selectedKBs,
        enable_web_search: useWebSearch,
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        intent: data.intent,
        confidence: data.confidence,
        sources: data.sources,
      }]);

      if (!currentSession && data.session_id) {
        setCurrentSession(data.session_id);
        fetchSessions();
      }
    } catch { /* silent */ }
  };

  const startNewChat = () => {
    setCurrentSession(null);
    setMessages([]);
    setSelectedKBs([]);
    setUseWebSearch(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const autoResize = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
  };

  const useSuggestion = (text) => {
    setMessage(text);
    if (inputRef.current) {
      inputRef.current.focus();
      setTimeout(() => autoResize({ target: inputRef.current }), 0);
    }
  };

  const toggleSources = (idx) =>
    setExpandedSources(prev => ({ ...prev, [idx]: !prev[idx] }));

  const fmt = (d) => new Date(d || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const kbLabel = selectedKBs.length === 0
    ? 'No KB selected'
    : selectedKBs.length === 1
      ? (knowledgeBases.find(k => k.id === selectedKBs[0])?.name ?? '1 KB')
      : `${selectedKBs.length} KBs`;

  return (
    <div className="chat-layout">
      {/* Sessions sidebar */}
      <div className="threads">
        <div className="threads-head">
          <button className="btn-new" onClick={startNewChat}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            New Chat
          </button>
          <div className="threads-search">
            <div className="search-wrap">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input className="search-input" type="text" placeholder="Search…"/>
            </div>
          </div>
        </div>

        <div className="threads-list">
          {sessions.length === 0 && (
            <div style={{ padding: 'var(--space-4)', fontSize: 'var(--text-sm)', color: 'var(--color-text-faint)' }}>
              No conversations yet.
            </div>
          )}
          {sessions.map(s => (
            <div
              key={s.id}
              className={`thread-item ${currentSession === s.id ? 'active' : ''}`}
              onClick={() => loadSession(s.id)}
            >
              <div className="thread-title">{s.title || `Chat ${s.id}`}</div>
              <div className="thread-meta">{s.created_at ? fmt(s.created_at) : 'Recent'}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div className="chat-main">
        {/* Topbar */}
        <div className="chat-topbar">
          <div className="kb-selector-container" onClick={e => e.stopPropagation()}>
            <div
              className={`kb-selector ${kbDropdownOpen ? 'active' : ''}`}
              onClick={() => setKbDropdownOpen(p => !p)}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
              </svg>
              <span>{kbLabel}</span>
              <svg className="chevron" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </div>

            <div className={`kb-dropdown ${kbDropdownOpen ? 'show' : ''}`}>
              <div className="thread-date-label" style={{ padding: '10px 12px 4px' }}>Select sources</div>
              <div className="kb-options-list">
                {knowledgeBases.length === 0 && !kbsLoading && (
                  <div style={{ padding: '10px 12px', fontSize: 'var(--text-sm)', color: 'var(--color-text-faint)' }}>
                    No knowledge bases found
                  </div>
                )}
                {knowledgeBases.map(kb => {
                  const sel = selectedKBs.includes(kb.id);
                  return (
                    <div
                      key={kb.id}
                      className={`kb-opt ${sel ? 'selected' : ''}`}
                      onClick={() =>
                        setSelectedKBs(sel
                          ? selectedKBs.filter(id => id !== kb.id)
                          : [...selectedKBs, kb.id]
                        )
                      }
                    >
                      <div className="kb-opt-check">
                        {sel && (
                          <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="4">
                            <polyline points="20 6 9 17 4 12"/>
                          </svg>
                        )}
                      </div>
                      <span className="kb-opt-name">{kb.name}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div
            className={`web-toggle ${useWebSearch ? 'on' : ''}`}
            onClick={() => setUseWebSearch(p => !p)}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="2" y1="12" x2="22" y2="12"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
            <div className="toggle-pill"/>
            Web Search
          </div>
        </div>

        {/* Messages */}
        <div className="chat-body">
          {messages.length === 0 && !loading && (
            <div className="empty-state">
              <div className="empty-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <p className="empty-title">Ask anything about your documents</p>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                Select a knowledge base above, then start a conversation.
              </p>
              <div className="suggestion-chips">
                {['Summarize my documents', 'What are the key topics?', 'Explain the main concepts'].map(s => (
                  <div key={s} className="chip" onClick={() => useSuggestion(s)}>{s}</div>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => {
            const isUser     = msg.role === 'user';
            const isExpanded = expandedSources[idx];

            return (
              <div
                key={idx}
                className="msg-wrapper"
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start',
                  marginBottom: 'var(--space-4)',
                }}
              >
                <div className={`msg-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
                  <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {msg.content}
                  </div>

                  {!isUser && (msg.confidence || msg.sources?.length > 0) && (
                    <div className="msg-meta">
                      {msg.confidence && (
                        <div style={{ marginBottom: 'var(--space-1)' }}>
                          <ConfidenceBadge score={msg.confidence} />
                        </div>
                      )}

                      {msg.sources?.length > 0 && (
                        <div>
                          <button
                            onClick={() => toggleSources(idx)}
                            style={{
                              background: 'none', border: 'none',
                              color: 'var(--color-primary)', fontSize: 'var(--text-xs)',
                              fontWeight: 600, cursor: 'pointer',
                              display: 'flex', alignItems: 'center', gap: 4, padding: 0,
                            }}
                          >
                            <svg
                              width="10" height="10" viewBox="0 0 24 24" fill="none"
                              stroke="currentColor" strokeWidth="3"
                              style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
                            >
                              <polyline points="6 9 12 15 18 9"/>
                            </svg>
                            {isExpanded ? 'Hide sources' : `${msg.sources.length} sources`}
                          </button>

                          {isExpanded && (
                            <div style={{ marginTop: 'var(--space-2)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                              {msg.sources.map((s, i) => (
                                <div
                                  key={i}
                                  style={{
                                    fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)',
                                    padding: '4px 8px',
                                    background: 'var(--color-surface-alt)',
                                    borderRadius: 'var(--radius-xs)',
                                    border: '1px solid var(--color-border)',
                                  }}
                                >
                                  {s?.title || `Source ${i + 1}`}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="msg-time">{fmt(msg.created_at)}</div>
                </div>
              </div>
            );
          })}

          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 'var(--space-4)' }}>
              <TypingIndicator />
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          {queryError && (
            <div style={{
              color: 'var(--color-error-text)', background: 'var(--color-error-bg)',
              fontSize: 'var(--text-sm)', padding: 'var(--space-2) var(--space-4)',
              borderRadius: 'var(--radius-sm)', marginBottom: 'var(--space-2)',
              border: '1px solid var(--color-error)',
            }}>
              {queryError}
            </div>
          )}
          <div className="input-wrap">
            <textarea
              ref={inputRef}
              className="chat-textarea"
              rows="1"
              placeholder="Ask a question… (Shift+Enter for new line)"
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={handleKey}
              onInput={autoResize}
            />
            <div className="input-actions">
              <button className="btn-send" onClick={handleSend} disabled={loading || !message.trim()}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
