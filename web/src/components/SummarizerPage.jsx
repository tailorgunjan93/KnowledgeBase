import React, { useState } from 'react';
import { apiClient } from '../api';

export function SummarizerPage({ user }) {
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSummarize = async () => {
    if (!text.trim() && !file) return;
    setLoading(true); setError(''); setSummary(null);
    try {
      let res;
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        res = await apiClient.post('/api/summarize/file', formData);
      } else {
        res = await apiClient.post('/api/summarize', { text });
      }
      if (res.data.error) { setError(res.data.error); }
      else { setSummary(res.data); }
    } catch (err) {
      console.error('Summarization Error:', err);
      const msg = err.response?.data?.detail || err.message || 'Summarization failed';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally { setLoading(false); }
  };

  const copyToClipboard = () => {
    if (summary?.summary) navigator.clipboard.writeText(summary.summary);
  };

  const resetSummarizer = () => {
    setText('');
    setFile(null);
    setSummary(null);
    setError('');
  };

  return (
    <div className="summarizer-content">
      <div className="input-section">
        <h2 className="brand-name" style={{fontSize: '24px', marginBottom: '8px'}}>Summarizer</h2>
        <p className="brand-sub" style={{paddingLeft: 0, marginBottom: '20px'}}>Condense complex documents into actionable insights instantly.</p>
        
        <textarea 
          placeholder="Paste your text here to summarize..."
          value={text} 
          onChange={e => setText(e.target.value)}
          disabled={!!file} 
        />
        
        <div className="upload-hint" style={{display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--surface2)', padding: '12px', borderRadius: '12px', border: '1px solid var(--border)'}}>
          <span style={{color: 'var(--ink)'}}>Or upload: </span>
          <input type="file" onChange={e => setFile(e.target.files[0])} style={{fontSize: '12px', color: 'var(--ink2)'}} />
          {file && (
            <button onClick={() => setFile(null)} className="kb-del-btn" style={{fontSize: '12px', padding: '2px 6px'}}>
              ✕ Clear
            </button>
          )}
        </div>

        {error && <div className="error-message" style={{textAlign: 'left', background: 'rgba(224,91,91,0.06)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(224,91,91,0.2)'}}>{error}</div>}

        <button onClick={handleSummarize} disabled={loading || (!text.trim() && !file)}>
          {loading ? (
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <div className="typing-dot" style={{width: '6px', height: '6px'}}></div>
              <span>Analyzing...</span>
            </div>
          ) : 'Summarize Document'}
        </button>
      </div>

      <div className="summary-result">
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px'}}>
          <h2 style={{margin: 0}}>Results</h2>
          <div style={{display: 'flex', gap: '8px'}}>
            {summary && (
              <>
                <button onClick={copyToClipboard} className="btn-logout" style={{padding: '6px 14px', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--ink)'}}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  Copy
                </button>
                <button onClick={resetSummarizer} className="btn-logout" style={{padding: '6px 14px', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--ink)'}}>
                  New
                </button>
              </>
            )}
          </div>
        </div>
        
        {!summary && !loading && (
           <div className="empty-state" style={{flex: 1}}>
              <div className="empty-icon" style={{width: '80px', height: '80px', borderRadius: '24px'}}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <p className="empty-title">Ready to Summarize</p>
              <p className="empty-sub">Paste text or upload a document to generate a concise summary.</p>
           </div>
        )}

        {loading && (
          <div className="empty-state" style={{flex: 1}}>
            <div className="upload-spinner" style={{width: '48px', height: '48px'}}></div>
            <p className="empty-sub" style={{marginTop: '20px', fontWeight: 500, color: 'var(--ink)'}}>Synthesizing key insights...</p>
            <p className="empty-sub" style={{fontSize: '12px'}}>This may take a few seconds depending on document length.</p>
          </div>
        )}

        {summary && (
          <div style={{animation: 'msgIn 0.5s ease both'}}>
            <div className="summary-text" style={{whiteSpace: 'pre-wrap'}}>{summary.summary}</div>
            
            {summary.key_points?.length > 0 && (
              <div className="key-points" style={{marginTop: '32px', background: 'var(--bg3)', padding: '24px', borderRadius: '16px', border: '1px solid var(--border)'}}>
                <h3 style={{fontSize: '12px', fontWeight: 600, color: 'var(--amber)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '1px'}}>Key Takeaways</h3>
                <ul style={{listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px'}}>
                  {summary.key_points.map((p, i) => (
                    <li key={i} style={{display: 'flex', gap: '12px', fontSize: '14px', color: 'var(--ink)', lineHeight: 1.6}}>
                      <span style={{color: 'var(--amber)', fontWeight: 600}}>•</span>
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div style={{display: 'flex', gap: '24px', fontSize: '11px', color: 'var(--ink3)', borderTop: '1px solid var(--border)', paddingTop: '20px', marginTop: '32px', textTransform: 'uppercase', letterSpacing: '0.5px'}}>
              <span>Original: {summary.original_length} chars</span>
              <span>Summary: {summary.summary_length} chars</span>
              <span style={{color: 'var(--green)', fontWeight: 600}}>Efficiency: {Math.round((1 - summary.summary_length / summary.original_length) * 100)}%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );

}