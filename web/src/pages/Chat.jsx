import React, { useState, useEffect, useRef } from 'react';
import { useRAGQuery } from '../hooks/useRAGQuery';
import { useDocuments } from '../hooks/useDocuments';
import { chatAPI } from '../api'; // Still need for sessions
import ConfidenceBadge from '../components/ConfidenceBadge';
import TypingIndicator from '../components/TypingIndicator';

export function ChatPage({ user }) {
  const [message, setMessage] = useState('');
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedKBs, setSelectedKBs] = useState([]);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [kbDropdownOpen, setKbDropdownOpen] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});

  const { query: runQuery, loading, error: queryError } = useRAGQuery();
  const { knowledgeBases, loading: kbsLoading, refresh: refreshKBs } = useDocuments();
  
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { 
    fetchSessions(); 
  }, []);

  useEffect(() => { 
    endRef.current?.scrollIntoView({ behavior: 'smooth' }); 
  }, [messages, loading]);

  const fetchSessions = async () => {
    try {
      const res = await chatAPI.getSessions();
      setSessions(res.data || []);
    } catch (err) { console.error('Failed to fetch sessions'); }
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
    const userMsg = message;
    setMessage('');
    
    if (inputRef.current) inputRef.current.style.height = 'auto';

    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    try {
      const data = await runQuery(userMsg, {
        session_id: currentSession,
        kb_ids: selectedKBs,
        enable_web_search: useWebSearch
      });
      
      setMessages(prev => [...prev, {
        role: 'assistant', 
        content: data.response,
        intent: data.intent, 
        confidence: data.confidence, 
        sources: data.sources
      }]);
      
      if (!currentSession && data.session_id) {
        setCurrentSession(data.session_id);
        fetchSessions();
      }
    } catch (err) {
      console.error('Chat error:', err);
    }
  };

  const toggleSources = (idx) => {
    setExpandedSources(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const startNewChat = () => {
    setCurrentSession(null); 
    setMessages([]); 
    setSelectedKBs([]); 
    setUseWebSearch(false);
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
                {knowledgeBases.length === 0 && !kbsLoading && <div className="kb-opt-empty" style={{padding: '12px', fontSize: '13px', color: 'var(--color-text-muted)'}}>No Knowledge Bases found</div>}
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
                        {isSelected && <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--color-surface)" strokeWidth="4"><polyline points="20 6 9 17 4 12"/></svg>}
                      </div>
                      <span className="kb-opt-name">{kb.name}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          
          <div className={`web-toggle ${useWebSearch ? 'on' : ''}`} onClick={() => setUseWebSearch(!useWebSearch)}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            <div className="toggle-pill"></div>
            Web Search
          </div>
        </div>

        <div className="chat-body">
          {messages.length === 0 && !loading && (
            <div className="empty-state">
              <div className="empty-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <p className="empty-title">Ask anything about your knowledge base</p>
              <div className="suggestion-chips">
                <div className="chip" onClick={() => useSuggestion('What is human nutrition?')}>What is human nutrition?</div>
                <div className="chip" onClick={() => useSuggestion('Summarize my documents')}>Summarize my documents</div>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            const isExpanded = expandedSources[idx];
            return (
              <div key={idx} className={`msg-wrapper ${isUser ? 'user-wrapper' : 'assistant-wrapper'}`} style={{
                display: 'flex',
                justifyContent: isUser ? 'flex-end' : 'flex-start',
                marginBottom: 'var(--space-6)',
                width: '100%'
              }}>
                <div className={`msg-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`} style={{
                  maxWidth: '75%',
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  background: isUser ? 'var(--color-primary)' : 'var(--color-surface-alt)',
                  color: isUser ? 'var(--color-surface)' : 'var(--color-text)',
                  boxShadow: 'var(--shadow-sm)',
                  position: 'relative'
                }}>
                  <div className="msg-text" style={{ fontSize: 'var(--text-base)', lineHeight: 1.5 }}>
                    {msg.content}
                  </div>
                  
                  {!isUser && (msg.confidence || msg.sources?.length > 0) && (
                    <div className="msg-meta" style={{ marginTop: 'var(--space-3)', borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                        <ConfidenceBadge score={msg.confidence} />
                      </div>
                      
                      {msg.sources?.length > 0 && (
                        <div className="sources-accordion">
                          <button 
                            onClick={() => toggleSources(idx)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: 'var(--color-primary)',
                              fontSize: 'var(--text-xs)',
                              fontWeight: 600,
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              padding: 0
                            }}
                          >
                            <svg 
                              width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"
                              style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s', marginRight: 4 }}
                            >
                              <polyline points="6 9 12 15 18 9"/>
                            </svg>
                            {isExpanded ? 'Hide Sources' : `Show ${msg.sources.length} Sources`}
                          </button>
                          
                          {isExpanded && (
                            <div className="sources-content" style={{ marginTop: 'var(--space-2)' }}>
                              {msg.sources.map((s, i) => (
                                <div key={i} style={{ 
                                  fontSize: 'var(--text-xs)', 
                                  color: 'var(--color-text-muted)',
                                  padding: '4px 8px',
                                  background: 'var(--color-surface)',
                                  borderRadius: 'var(--radius-sm)',
                                  marginBottom: '4px',
                                  border: '1px solid var(--color-border)'
                                }}>
                                  {s.title || 'Source'}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="msg-time" style={{ fontSize: '10px', opacity: 0.7, marginTop: '4px', textAlign: 'right' }}>{now()}</div>
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="assistant-wrapper" style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 'var(--space-6)' }}>
              <TypingIndicator />
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="chat-input-area">
          {queryError && <div className="error-message" style={{ color: 'var(--color-error)', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-2)' }}>{queryError}</div>}
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
              <button className="btn-send" onClick={handleSend} disabled={loading || !message.trim()}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              </button>
            </div>
          </div>
         </div>
       </div>
     </div>
   );
}