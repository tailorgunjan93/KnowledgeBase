import { useState, useEffect, useRef } from 'react';
import { useRAGQuery } from '../hooks/useRAGQuery';
import { useDocuments } from '../hooks/useDocuments';
import { chatAPI } from '../api';
import { httpClient } from '../api/httpClient';
import ConfidenceBadge from '../components/ConfidenceBadge';
import TypingIndicator from '../components/TypingIndicator';

export function ChatPage({ currentSession, setCurrentSession, onSessionCreated }) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [selectedKBs, setSelectedKBs] = useState([]);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [kbDropdownOpen, setKbDropdownOpen] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});

  // Summarizer panel state
  const [showSummarizer, setShowSummarizer] = useState(false);
  const [sumText, setSumText] = useState('');
  const [sumFile, setSumFile] = useState(null);
  const [sumResult, setSumResult] = useState(null);
  const [sumLoading, setSumLoading] = useState(false);
  const [sumError, setSumError] = useState('');
  const [sumCopied, setSumCopied] = useState(false);

  // Upload doc to KB
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadKB, setUploadKB] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');
  const uploadInputRef = useRef(null);

  const { query: runQuery, loading, error: queryError } = useRAGQuery();
  const { knowledgeBases } = useDocuments();

  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  useEffect(() => {
    const close = () => setKbDropdownOpen(false);
    if (kbDropdownOpen) document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [kbDropdownOpen]);

  // Load messages when session changes
  useEffect(() => {
    if (currentSession) {
      chatAPI.getMessages(currentSession)
        .then(res => setMessages(res.data || []))
        .catch(() => {});
    } else {
      setMessages([]);
    }
  }, [currentSession]);

  const handleSend = async () => {
    if (!message.trim() || loading) return;
    const userMsg = message;
    setMessage('');
    if (inputRef.current) inputRef.current.style.height = 'auto';

    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);

    // Add a placeholder assistant message
    setMessages(prev => [...prev, { role: 'assistant', content: '', loading: true }]);

    try {
      const data = await runQuery(userMsg, {
        session_id: currentSession,
        kb_ids: selectedKBs,
        enable_web_search: useWebSearch,
      }, (update) => {
        setMessages(prev => {
          const newMsgs = [...prev];
          const lastMsg = newMsgs[newMsgs.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content = update.content;
            lastMsg.loading = false;
            if (update.isMeta) {
              lastMsg.sources = update.sources;
              lastMsg.session_id = update.session_id;
            }
          }
          return newMsgs;
        });
      });

      if (!currentSession && data.session_id) {
        setCurrentSession(data.session_id);
        onSessionCreated?.();
      }
    } catch { /* silent */ }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const autoResize = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
  };

  const toggleSources = (idx) =>
    setExpandedSources(prev => ({ ...prev, [idx]: !prev[idx] }));

  const fmt = (d) => new Date(d || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const kbLabel = selectedKBs.length === 0
    ? 'No KB selected'
    : selectedKBs.length === 1
      ? (knowledgeBases.find(k => k.id === selectedKBs[0])?.name ?? '1 KB')
      : `${selectedKBs.length} KBs`;

  // Summarizer logic
  const handleSummarize = async () => {
    if (!sumText.trim() && !sumFile) return;
    setSumLoading(true); setSumError(''); setSumResult(null);
    try {
      let res;
      if (sumFile) {
        const fd = new FormData();
        fd.append('file', sumFile);
        res = await httpClient.post('/api/summarize/file', fd);
      } else {
        res = await httpClient.post('/api/summarize', { text: sumText });
      }
      setSumResult(res.data);
    } catch (err) {
      setSumError(err.message || 'Summarization failed');
    } finally {
      setSumLoading(false);
    }
  };

  const copySummary = () => {
    if (!sumResult?.summary) return;
    navigator.clipboard.writeText(sumResult.summary).then(() => {
      setSumCopied(true);
      setTimeout(() => setSumCopied(false), 2000);
    });
  };

  // Upload doc logic
  const handleUpload = async () => {
    if (!uploadFile || !uploadKB) return;
    setUploadLoading(true); setUploadMsg('');
    try {
      const fd = new FormData();
      fd.append('file', uploadFile);
      await httpClient.post(`/api/kb/${uploadKB}/documents`, fd);
      setUploadMsg('Uploaded successfully!');
      setUploadFile(null);
      if (uploadInputRef.current) uploadInputRef.current.value = '';
    } catch (err) {
      setUploadMsg('Upload failed: ' + (err.message || 'unknown error'));
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div className="chat-main">
      {/* Topbar */}
      <div className="chat-topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flex: 1 }}>
          {/* KB selector */}
          <div className="kb-selector-container" onClick={e => e.stopPropagation()}>
            <div className={`kb-selector ${kbDropdownOpen ? 'active' : ''}`} onClick={() => setKbDropdownOpen(p => !p)}>
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
                {knowledgeBases.length === 0 && (
                  <div style={{ padding: '10px 12px', fontSize: 'var(--text-sm)', color: 'var(--color-text-faint)' }}>
                    No knowledge bases found
                  </div>
                )}
                {knowledgeBases.map(kb => {
                  const sel = selectedKBs.includes(kb.id);
                  return (
                    <div key={kb.id} className={`kb-opt ${sel ? 'selected' : ''}`}
                      onClick={() => setSelectedKBs(sel ? selectedKBs.filter(id => id !== kb.id) : [...selectedKBs, kb.id])}>
                      <div className="kb-opt-check">
                        {sel && <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="4"><polyline points="20 6 9 17 4 12"/></svg>}
                      </div>
                      <span className="kb-opt-name">{kb.name}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Upload button */}
          <button
            className={`topbar-btn ${showUpload ? 'topbar-btn-active' : ''}`}
            onClick={() => { setShowUpload(p => !p); setShowSummarizer(false); }}
            title="Upload document"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload
          </button>

          {/* Summarizer button */}
          <button
            className={`topbar-btn ${showSummarizer ? 'topbar-btn-active' : ''}`}
            onClick={() => { setShowSummarizer(p => !p); setShowUpload(false); }}
            title="Summarize text or file"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            Summarize
          </button>
        </div>

        {/* Web search toggle */}
        <div className={`web-toggle ${useWebSearch ? 'on' : ''}`} onClick={() => setUseWebSearch(p => !p)}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          </svg>
          <div className="toggle-pill"/>
          Web Search
        </div>
      </div>

      {/* Summarizer slide-in panel */}
      {showSummarizer && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <span>Summarizer</span>
            <button className="chat-panel-close" onClick={() => { setShowSummarizer(false); setSumResult(null); setSumText(''); setSumFile(null); setSumError(''); }}>✕</button>
          </div>
          <div className="chat-panel-body">
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <textarea
                className="summarizer-textarea"
                style={{ minHeight: 100, flex: 'none' }}
                placeholder="Paste text to summarize…"
                value={sumText}
                onChange={e => setSumText(e.target.value)}
                disabled={!!sumFile || sumLoading}
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                <label className="topbar-btn" style={{ cursor: 'pointer' }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                  {sumFile ? sumFile.name : 'Upload file'}
                  <input type="file" accept=".pdf,.docx,.doc,.txt,.md" style={{ display: 'none' }}
                    onChange={e => { setSumFile(e.target.files[0] || null); setSumText(''); }} disabled={sumLoading} />
                </label>
                {sumFile && (
                  <button onClick={() => setSumFile(null)} style={{ background: 'none', border: 'none', color: 'var(--color-error)', cursor: 'pointer', fontSize: 'var(--text-xs)', fontWeight: 600 }}>
                    ✕ Remove
                  </button>
                )}
                <button className="btn-summarize" style={{ marginLeft: 'auto' }} onClick={handleSummarize} disabled={!sumText.trim() && !sumFile || sumLoading}>
                  {sumLoading ? <><div className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }}/> Generating…</> : 'Summarize'}
                </button>
              </div>
              {sumError && <div style={{ color: 'var(--color-error-text)', fontSize: 'var(--text-xs)' }}>{sumError}</div>}
              {sumResult && (
                <div style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3)', fontSize: 'var(--text-sm)', lineHeight: 1.6, position: 'relative' }}>
                  <button className="btn-copy" style={{ position: 'absolute', top: 8, right: 8 }} onClick={copySummary}>{sumCopied ? '✓ Copied' : 'Copy'}</button>
                  <p style={{ paddingRight: 60, whiteSpace: 'pre-wrap' }}>{sumResult.summary}</p>
                  {sumResult.key_points?.length > 0 && (
                    <ul style={{ marginTop: 'var(--space-3)', paddingLeft: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                      {sumResult.key_points.map((pt, i) => <li key={i} style={{ fontSize: 'var(--text-xs)' }}>{pt}</li>)}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Upload panel */}
      {showUpload && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <span>Upload Document to Knowledge Base</span>
            <button className="chat-panel-close" onClick={() => { setShowUpload(false); setUploadFile(null); setUploadMsg(''); }}>✕</button>
          </div>
          <div className="chat-panel-body">
            <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', flex: 1, minWidth: 160 }}>
                <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-muted)' }}>Knowledge Base</label>
                <select
                  value={uploadKB}
                  onChange={e => setUploadKB(e.target.value)}
                  style={{ padding: '6px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--color-border)', background: 'var(--color-surface-alt)', color: 'var(--color-text)', fontSize: 'var(--text-sm)', fontFamily: 'inherit' }}
                >
                  <option value="">Select KB…</option>
                  {knowledgeBases.map(kb => <option key={kb.id} value={kb.id}>{kb.name}</option>)}
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', flex: 2, minWidth: 200 }}>
                <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-muted)' }}>File</label>
                <label className="topbar-btn" style={{ cursor: 'pointer', width: 'fit-content' }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                  {uploadFile ? uploadFile.name : 'Choose file'}
                  <input ref={uploadInputRef} type="file" accept=".pdf,.doc,.docx,.txt,.md,.xlsx,.xls" style={{ display: 'none' }}
                    onChange={e => { setUploadFile(e.target.files[0] || null); setUploadMsg(''); }} />
                </label>
              </div>
              <button className="btn-summarize" onClick={handleUpload} disabled={!uploadFile || !uploadKB || uploadLoading}>
                {uploadLoading ? <><div className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }}/> Uploading…</> : 'Upload'}
              </button>
            </div>
            {uploadMsg && (
              <div style={{ marginTop: 'var(--space-2)', fontSize: 'var(--text-xs)', color: uploadMsg.startsWith('Upload failed') ? 'var(--color-error-text)' : 'var(--color-success)' }}>
                {uploadMsg}
              </div>
            )}
          </div>
        </div>
      )}

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
                <div key={s} className="chip" onClick={() => { setMessage(s); inputRef.current?.focus(); }}>{s}</div>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          const isExpanded = expandedSources[idx];
          return (
            <div key={idx} className="msg-wrapper" style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 'var(--space-4)' }}>
              <div className={`msg-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{msg.content}</div>

                {!isUser && (msg.confidence || msg.sources?.length > 0) && (
                  <div className="msg-meta">
                    {msg.confidence && <div style={{ marginBottom: 'var(--space-1)' }}><ConfidenceBadge score={msg.confidence} /></div>}
                    {msg.sources?.length > 0 && (
                      <div>
                        <button onClick={() => toggleSources(idx)} style={{ background: 'none', border: 'none', color: 'var(--color-primary)', fontSize: 'var(--text-xs)', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, padding: 0 }}>
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
                            <polyline points="6 9 12 15 18 9"/>
                          </svg>
                          {isExpanded ? 'Hide sources' : `${msg.sources.length} sources`}
                        </button>
                        {isExpanded && (
                          <div style={{ marginTop: 'var(--space-2)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                            {msg.sources.map((s, i) => (
                              <div key={i} style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', padding: '4px 8px', background: 'var(--color-surface-alt)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--color-border)' }}>
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

        {loading && messages[messages.length - 1]?.content === '' && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 'var(--space-4)' }}>
            <TypingIndicator />
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        {queryError && (
          <div style={{ color: 'var(--color-error-text)', background: 'var(--color-error-bg)', fontSize: 'var(--text-sm)', padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-sm)', marginBottom: 'var(--space-2)', border: '1px solid var(--color-error)' }}>
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
  );
}
