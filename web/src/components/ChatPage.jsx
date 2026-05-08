import React, { useState, useEffect, useRef } from 'react';
import { kbAPI, chatAPI } from '../api';

export function ChatPage({ user }) {
  const [message, setMessage] = useState('');
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKBs, setSelectedKBs] = useState([]);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [kbDropdownOpen, setKbDropdownOpen] = useState(false);
  
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { fetchSessions(); fetchKBs(); }, []);

  useEffect(() => { 
    endRef.current?.scrollIntoView({ behavior: 'smooth' }); 
  }, [messages, loading]);

  const fetchSessions = async () => {
    try {
      const res = await chatAPI.getSessions();
      setSessions(res.data || []);
    } catch (err) { console.error('Failed to fetch sessions'); }
  };

  const fetchKBs = async () => {
    try {
      const res = await kbAPI.list();
      const items = res.data.items || [];
      setKnowledgeBases(items);
      if (items.length > 0 && selectedKBs.length === 0) {
        setSelectedKBs([items[0].id]);
      }
    } catch (err) { console.error('Failed to fetch KBs'); }
  };

  const loadSession = async (sessionId) => {
    try {
      const res = await chatAPI.getMessages(sessionId);
      setMessages(res.data || []);
      setCurrentSession(sessionId);
    } catch (err) { console.error('Failed to load session'); }
  };

  const handleSend = async () => {
    if (!message.trim()) return;
    setError('');
    setLoading(true);
    const userMsg = message;
    setMessage('');
    
    // Auto-reset textarea height
    if (inputRef.current) inputRef.current.style.height = 'auto';

    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    try {
      const res = await chatAPI.chat(userMsg, currentSession, selectedKBs, useWebSearch);
      setMessages(prev => [...prev, {
        role: 'assistant', content: res.data.response,
        intent: res.data.intent, confidence: res.data.confidence, sources: res.data.sources
      }]);
      if (!currentSession && res.data.session_id) {
        setCurrentSession(res.data.session_id);
        fetchSessions();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally { setLoading(false); }
  };

  const startNewChat = () => {
    setCurrentSession(null); setMessages([]); setSelectedKBs([]); setUseWebSearch(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!loading && message.trim()) handleSend();
    }
  };

  const autoResize = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
  };

  const useSuggestion = (text) => {
    setMessage(text);
    if (inputRef.current) {
      inputRef.current.value = text;
      autoResize({ target: inputRef.current });
      inputRef.current.focus();
    }
  };

  const now = () => new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });

  // Render Theme Toggle is already in Sidebar, but user mock had it in Topbar. We can keep it in Sidebar or add it here.
  // We'll add the theme toggle here to match the user's mockup.
  const [theme, setTheme] = useState(() => localStorage.getItem('kbase-theme') || 'dark');
  const handleTheme = (t) => {
    setTheme(t);
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem('kbase-theme', t);
  };

  return (
    <div className="chat-layout">
      <div className="threads">
        <div className="threads-head">
          <button className="btn-new" onClick={startNewChat}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            New Chat
          </button>
        </div>
        <div className="threads-search">
          <div className="search-wrap">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input className="search-input" type="text" placeholder="Search conversations…"/>
          </div>
        </div>
        <div className="threads-list">
          {sessions.map(s => (
            <div key={s.id}
                 className={`thread-item ${currentSession === s.id ? 'active' : ''}`}
                 onClick={() => loadSession(s.id)}>
              <div className="thread-title">{s.title || `Chat ${s.id}`}</div>
              <div className="thread-meta">Recent</div>
            </div>
          ))}
        </div>
      </div>

      <div className="chat-main">
        <div className="chat-topbar">
          <div className="kb-selector-container">
            <div className={`kb-selector ${kbDropdownOpen ? 'active' : ''}`} onClick={() => setKbDropdownOpen(!kbDropdownOpen)}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
              <span>
                {selectedKBs.length === 0 ? 'No Knowledge Base' : 
                 selectedKBs.length === 1 ? knowledgeBases.find(k => k.id === selectedKBs[0])?.name : 
                 `${selectedKBs.length} Selected`}
              </span>
              <svg className="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            
            <div className={`kb-dropdown ${kbDropdownOpen ? 'show' : ''}`}>
              <div className="nav-section-label" style={{padding: '8px 12px'}}>Select Sources</div>
              <div className="kb-options-list">
                {knowledgeBases.length === 0 && <div className="kb-opt-empty" style={{padding: '12px', fontSize: '13px', color: 'var(--ink3)'}}>No Knowledge Bases found</div>}
                {knowledgeBases.map(kb => {
                  const isSelected = selectedKBs.includes(kb.id);
                  return (
                    <div key={kb.id} 
                         className={`kb-opt ${isSelected ? 'selected' : ''}`}
                         onClick={(e) => {
                           e.stopPropagation();
                           if (isSelected) setSelectedKBs(selectedKBs.filter(id => id !== kb.id));
                           else setSelectedKBs([...selectedKBs, kb.id]);
                         }}>
                      <div className="kb-opt-check">
                        {isSelected && <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--bg)" strokeWidth="4"><polyline points="20 6 9 17 4 12"/></svg>}
                      </div>
                      <span className="kb-opt-name">{kb.name}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          
          {kbDropdownOpen && <div className="dropdown-overlay" onClick={() => setKbDropdownOpen(false)} style={{position: 'fixed', inset: 0, zIndex: 90}} />}
          <div className={`web-toggle ${useWebSearch ? 'on' : ''}`} onClick={() => setUseWebSearch(!useWebSearch)}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            <div className="toggle-pill"></div>
            Web Search
          </div>
          <div className="topbar-spacer"></div>
          <div className="theme-toggle-top">
            <button className={`t-btn ${theme === 'light' ? 'active' : ''}`} onClick={() => handleTheme('light')} title="Light">☀️</button>
            <button className={`t-btn ${theme === 'dark' ? 'active' : ''}`} onClick={() => handleTheme('dark')} title="Dark">🌙</button>
          </div>
        </div>

        <div className="chat-body">
          {messages.length === 0 && !loading && (
            <div className="empty-state">
              <div className="empty-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <p className="empty-title">Start a conversation</p>
              <p className="empty-sub">Ask anything or choose a suggestion below to begin</p>
              <div className="suggestion-chips">
                <div className="chip" onClick={() => useSuggestion('What is human nutrition?')}>What is human nutrition?</div>
                <div className="chip" onClick={() => useSuggestion('Summarize my documents')}>Summarize my documents</div>
                <div className="chip" onClick={() => useSuggestion('How does the knowledge base work?')}>How does the knowledge base work?</div>
                <div className="chip" onClick={() => useSuggestion('Help me research a topic')}>Help me research a topic</div>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            return (
              <div key={idx} className={`msg ${isUser ? 'user' : 'assistant'}`}>
                <div className="msg-avatar">{isUser ? 'U' : '🤖'}</div>
                <div className="msg-content">
                  <div className="msg-name">{isUser ? 'You' : 'KBase AI'}</div>
                  <div className="msg-bubble">
                    {msg.content}
                    {!isUser && (msg.confidence || msg.sources?.length > 0) && (
                      <div className="msg-extra">
                        {msg.confidence && (
                          <div className="confidence-tag">
                            <div className="conf-bar">
                              <div className="conf-fill" style={{
                                width: typeof msg.confidence === 'string' 
                                  ? msg.confidence 
                                  : `${msg.confidence * 100}%`
                              }}></div>
                            </div>
                            <span>{msg.confidence}{typeof msg.confidence === 'number' ? '%' : ''} confidence</span>
                          </div>
                        )}
                        {msg.sources?.length > 0 && (
                          <div className="sources-list">
                            {msg.sources.map((s, i) => (
                              <div key={i} className="source-tag">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                {s.title || 'Source'}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="msg-time">{now()}</div>
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="msg assistant">
              <div className="msg-avatar">🤖</div>
              <div className="msg-content">
                <div className="msg-name">KBase AI</div>
                <div className="msg-bubble">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div><div className="typing-dot"></div><div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="chat-input-area">
          {error && <div className="error-message" style={{marginBottom: '10px'}}>{error}</div>}
          <div className="input-wrap">
            <textarea
              ref={inputRef}
              className="chat-textarea"
              rows="1"
              placeholder="Ask a question…"
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={handleKey}
              onInput={autoResize}
            ></textarea>
            <div className="input-actions">
              <button className="icon-btn" title="Attach file">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
              </button>
              <button className="btn-send" onClick={handleSend} disabled={loading || !message.trim()}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              </button>
            </div>
          </div>
          <p className="input-hint">Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line</p>
        </div>
      </div>
    </div>
  );

}