import { useState, useEffect, useRef } from 'react';
import { useRAGQuery } from '../hooks/useRAGQuery';
import { useDocuments } from '../hooks/useDocuments';
import { chatAPI } from '../api';
import { httpClient } from '../api/httpClient';
import ConfidenceBadge from '../components/ConfidenceBadge';
import { PipelineProgress } from '../components/PipelineProgress';

export function ChatPage({ currentSession, setCurrentSession, onSessionCreated }) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [streamStatus, setStreamStatus]     = useState(null);
  const [pipelineMode, setPipelineMode]     = useState('general');
  const [pipelineHistory, setPipelineHistory] = useState(new Set());
  const [selectedKBs, setSelectedKBs] = useState([]);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [useAdvancedRAG, setUseAdvancedRAG] = useState(false);
  const [kbDropdownOpen, setKbDropdownOpen] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const [previewSource, setPreviewSource] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewType, setPreviewType] = useState('');
  const skipNextLoad = useRef(false); // Prevents API reload when creating a new session

  const handleSourceClick = (s) => {
    if (s.type === 'web') {
      window.open(s.url, '_blank');
    } else {
      setPreviewSource(s);
    }
  };

  useEffect(() => {
    if (!previewSource?.doc_id) {
      setPreviewUrl(null);
      setPreviewType('');
      return;
    }

    let url = null;
    const fetchFile = async () => {
      setPreviewLoading(true);
      try {
        const res = await httpClient.get(`/api/documents/${previewSource.doc_id}/file`, {
          responseType: 'blob'
        });
        const contentType = res.headers['content-type'] || 'application/octet-stream';
        setPreviewType(contentType);
        
        // Ensure the blob has the correct type
        const blob = new Blob([res.data], { type: contentType });
        url = URL.createObjectURL(blob);
        setPreviewUrl(url);
      } catch (err) {
        console.error('Failed to fetch preview file:', err);
      } finally {
        setPreviewLoading(false);
      }
    };

    fetchFile();
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [previewSource]);

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

  // Track which pipeline statuses have been seen (for step "done" state)
  useEffect(() => {
    if (streamStatus) {
      setPipelineHistory(prev => {
        const next = new Set(prev);
        next.add(streamStatus);
        return next;
      });
    } else {
      setPipelineHistory(new Set());
    }
  }, [streamStatus]);

  // Load messages when session changes (but skip when WE just created a new session)
  useEffect(() => {
    setPreviewSource(null);
    setStreamStatus(null);
    if (skipNextLoad.current) {
      skipNextLoad.current = false;
      return;
    }
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
    setMessages(prev => [...prev, { role: 'assistant', content: '', loading: true }]);

    // Set pipeline mode and reset history before the request
    const mode = selectedKBs.length > 0
      ? (useAdvancedRAG ? 'kb_advanced' : 'kb_simple')
      : useWebSearch ? 'web' : 'general';
    setPipelineMode(mode);
    setPipelineHistory(new Set());

    // Show status immediately (don't wait for backend — network timing is unreliable)
    if (selectedKBs.length > 0) {
      setStreamStatus('🔍 Searching knowledge base...');
    } else if (useWebSearch) {
      setStreamStatus('🌐 Searching the web...');
    } else {
      setStreamStatus('🧠 Thinking...');
    }

    try {
      const data = await runQuery(userMsg, {
        session_id: currentSession,
        kb_ids: selectedKBs,
        enable_web_search: useWebSearch,
        advanced_rag: useAdvancedRAG,
      }, (update) => {
        // Update status from backend for richer step info
        if (update.status !== undefined) {
          setStreamStatus(update.status || null);
        }
        // Update session ID as soon as it's available (fixes "attached to older chat" UX)
        if (update.session_id && !currentSession) {
          skipNextLoad.current = true;
          setCurrentSession(update.session_id);
          onSessionCreated?.();
        }

        if (update.content !== undefined || update.isMeta) {
          // Clear thinking indicator once real content starts
          if (update.content && update.content.trim().length > 0) {
            setStreamStatus(null);
          }
          setMessages(prev => {
            const newMsgs = [...prev];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg && lastMsg.role === 'assistant') {
              if (update.content !== undefined) {
                lastMsg.content = update.content;
                lastMsg.loading = false;
              }
              if (update.isMeta) {
                lastMsg.sources = update.sources;
              }
            }
            return newMsgs;
          });
        }
      });

      setStreamStatus(null); 
      if (!currentSession && data?.session_id) {
        skipNextLoad.current = true;
        setCurrentSession(data.session_id);
        onSessionCreated?.();
      }
    } catch { 
      setStreamStatus(null);
    }
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
    <div className="chat-layout-container" style={{ display: 'flex', flex: 1, width: '100%', overflow: 'hidden' }}>
      <div className="chat-main" style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
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

          {/* Advanced RAG toggle */}
          <div className={`web-toggle ${useAdvancedRAG ? 'on' : ''}`} onClick={() => setUseAdvancedRAG(p => !p)} style={{ marginLeft: 8 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"/>
              <line x1="16" y1="8" x2="2" y2="22"/>
              <line x1="17.5" y1="15" x2="9" y2="15"/>
            </svg>
            <div className="toggle-pill"/>
            Advanced RAG
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
                  <div style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-4)', fontSize: 'var(--text-base)', lineHeight: 1.8, position: 'relative', overflowY: 'auto' }}>
                    <button className="btn-copy" style={{ position: 'absolute', top: 8, right: 8 }} onClick={copySummary}>{sumCopied ? '✓ Copied' : 'Copy'}</button>
                    <p style={{ paddingRight: 64, whiteSpace: 'pre-wrap', marginBottom: sumResult.key_points?.length > 0 ? 'var(--space-3)' : 0 }}>{sumResult.summary}</p>
                    {sumResult.key_points?.length > 0 && (
                      <div style={{ background: 'var(--color-primary-light)', borderLeft: '3px solid var(--color-primary)', borderRadius: 'var(--radius-xs)', padding: 'var(--space-3) var(--space-4)' }}>
                        <div style={{ fontSize: 'var(--text-xs)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-primary)', marginBottom: 'var(--space-2)' }}>Key Takeaways</div>
                        <ul style={{ paddingLeft: 'var(--space-5)', margin: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                          {sumResult.key_points.map((pt, i) => <li key={i} style={{ fontSize: 'var(--text-sm)', lineHeight: 1.65 }}>{pt}</li>)}
                        </ul>
                      </div>
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
                  {msg.status && (
                    <div style={{ 
                      display: 'flex', alignItems: 'center', gap: 8, 
                      marginBottom: 12, padding: '8px 12px', 
                      background: 'rgba(var(--color-primary-rgb), 0.05)', 
                      borderRadius: 'var(--radius-sm)', border: '1px solid rgba(var(--color-primary-rgb), 0.1)',
                      fontSize: 'var(--text-xs)', color: 'var(--color-primary)', fontWeight: 500,
                      animation: 'pulse 2s infinite'
                    }}>
                      <div className="spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />
                      {msg.status}
                    </div>
                  )}
                  {msg.loading && !msg.content ? (
                    <>
                      <div className="skeleton-line w-100" />
                      <div className="skeleton-line w-85" />
                      <div className="skeleton-line w-70" />
                      <div className="skeleton-line w-45" />
                    </>
                  ) : (
                    <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{msg.content}</div>
                  )}

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
                            <div className="citation-chips">
                              {msg.sources.map((s, i) => {
                                const pct = s?.score != null ? Math.round(s.score * 100) : null;
                                const scoreClass = pct == null ? ''
                                  : pct >= 85 ? 'score-high'
                                  : pct >= 70 ? 'score-mid'
                                  : 'score-low';
                                return (
                                  <div key={i} className="citation-chip" onClick={() => handleSourceClick(s)}>
                                    <span>{s?.type === 'web' ? '🌐' : '📄'}</span>
                                    <span className="citation-chip-name">{s?.title || `Source ${i + 1}`}</span>
                                    {pct != null && (
                                      <span className={`citation-score ${scoreClass}`}>{pct}%</span>
                                    )}
                                  </div>
                                );
                              })}
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

          {/* Pipeline progress — step-by-step RAG visualization */}
          {streamStatus && (
            <PipelineProgress
              currentStatus={streamStatus}
              seenStatuses={pipelineHistory}
              mode={pipelineMode}
            />
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

      {/* Source Preview */}
      {previewSource && (
        <div className="source-preview-panel" style={{ width: 450, borderLeft: '1px solid var(--color-border)', display: 'flex', flexDirection: 'column' }}>
          <div className="chat-panel-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, flex: 1 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
              </svg>
              <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: 'var(--text-sm)' }}>
                {previewSource.title}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {previewUrl && (
                <a href={previewUrl} download={previewSource.title} className="chat-panel-close" style={{ fontSize: 12, display: 'flex', alignItems: 'center', color: 'var(--color-primary)', textDecoration: 'none' }} title="Download File">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                </a>
              )}
              <button className="chat-panel-close" onClick={() => setPreviewSource(null)}>✕</button>
            </div>
          </div>
          <div style={{ flex: 1, position: 'relative', background: '#f5f5f5', display: 'flex', flexDirection: 'column' }}>
            {previewLoading && (
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.8)', zIndex: 5 }}>
                <div className="spinner" style={{ width: 24, height: 24 }} />
              </div>
            )}
            {previewUrl ? (
              (previewType === 'application/pdf' || previewType.startsWith('text/') || previewType.startsWith('image/')) ? (
                <iframe 
                  src={`${previewUrl}#page=${previewSource.metadata?.page || 1}`}
                  style={{ width: '100%', height: '100%', border: 'none' }}
                  title="Document Preview"
                />
              ) : (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, padding: 32, textAlign: 'center' }}>
                  <div style={{ padding: 20, background: 'var(--color-surface)', borderRadius: '50%' }}>
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-faint)" strokeWidth="1.5">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                    </svg>
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>Preview unavailable</div>
                    <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>This file type cannot be displayed directly in the browser.</div>
                  </div>
                  <a href={previewUrl} download={previewSource.title} className="btn-summarize" style={{ textDecoration: 'none' }}>
                    Download to View
                  </a>
                </div>
              )
            ) : (
              !previewLoading && <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-text-muted)' }}>Failed to load document preview.</div>
            )}
          </div>
          <div style={{ padding: '16px', background: 'var(--color-surface)', borderTop: '1px solid var(--color-border)', fontSize: 'var(--text-xs)' }}>
            <div style={{ fontWeight: 700, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Cited Content</div>
            <div style={{ color: 'var(--color-text)', lineHeight: 1.5, maxHeight: '120px', overflowY: 'auto', fontStyle: 'italic', borderLeft: '3px solid var(--color-primary)', paddingLeft: 12 }}>
              "{previewSource.text}"
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
