import React, { useState } from 'react';
import { httpClient } from '../api/httpClient';

export function SummarizerPage({ user }) {
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSummarize = async () => {
    if (!text.trim() && !file) return;
    setLoading(true); 
    setError(''); 
    setSummary(null);
    try {
      let res;
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        res = await httpClient.post('/api/summarize/file', formData);
      } else {
        res = await httpClient.post('/api/summarize', { text });
      }
      setSummary(res.data);
    } catch (err) {
      console.error('Summarization Error:', err);
      setError(err.message || 'Summarization failed');
    } finally { 
      setLoading(false); 
    }
  };

  const copyToClipboard = () => {
    if (summary?.summary) {
      navigator.clipboard.writeText(summary.summary);
      alert('Copied to clipboard!');
    }
  };

  return (
    <div className="summarizer-layout" style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%', 
      background: 'var(--color-surface-alt)',
      padding: 'var(--space-8)'
    }}>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, marginBottom: 'var(--space-2)' }}>Summarizer</h1>
        <p style={{ color: 'var(--color-text-muted)' }}>Transform long documents into concise, actionable summaries.</p>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1.5fr', 
        gap: 'var(--space-8)', 
        flex: 1, 
        overflow: 'hidden' 
      }}>
        {/* Input section */}
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: 'var(--space-4)',
          background: 'var(--color-surface)',
          padding: 'var(--space-6)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-md)'
        }}>
          <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>Input</h3>
          
          <textarea 
            placeholder="Paste your text here to summarize..."
            value={text} 
            onChange={e => setText(e.target.value)}
            disabled={!!file || loading} 
            style={{ 
              flex: 1, 
              padding: 'var(--space-4)', 
              borderRadius: 'var(--radius-md)', 
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface-alt)',
              color: 'inherit',
              fontFamily: 'inherit',
              fontSize: 'var(--text-sm)',
              resize: 'none',
              outline: 'none'
            }}
          />

          <div style={{ 
            padding: 'var(--space-4)', 
            borderRadius: 'var(--radius-md)', 
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface-alt)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-2)'
          }}>
            <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600 }}>Or upload a file:</span>
            <input 
              type="file" 
              onChange={e => setFile(e.target.files[0])} 
              disabled={loading}
              style={{ fontSize: 'var(--text-xs)' }} 
            />
            {file && (
              <button 
                onClick={() => setFile(null)} 
                style={{ alignSelf: 'flex-start', background: 'none', border: 'none', color: 'var(--color-error)', cursor: 'pointer', fontSize: 'var(--text-xs)' }}
              >
                ✕ Remove File
              </button>
            )}
          </div>

          <button 
            onClick={handleSummarize} 
            disabled={loading || (!text.trim() && !file)}
            style={{ 
              padding: 'var(--space-3)', 
              background: 'var(--color-primary)', 
              color: 'white', 
              border: 'none', 
              borderRadius: 'var(--radius-md)',
              fontWeight: 600,
              cursor: 'pointer',
              opacity: loading || (!text.trim() && !file) ? 0.6 : 1,
              transition: 'all 0.2s'
            }}
          >
            {loading ? 'Synthesizing...' : 'Summarize'}
          </button>

          {error && <div style={{ color: 'var(--color-error)', fontSize: 'var(--text-xs)', padding: 'var(--space-2)' }}>{error}</div>}
        </div>

        {/* Output section */}
        <div style={{ 
          background: 'var(--color-surface)',
          padding: 'var(--space-6)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-md)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>Summary Result</h3>
            {summary && (
              <button 
                onClick={copyToClipboard}
                style={{ background: 'none', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '4px 8px', fontSize: 'var(--text-xs)', cursor: 'pointer' }}
              >
                Copy Text
              </button>
            )}
          </div>

          <div style={{ flex: 1, overflowY: 'auto' }}>
            {!summary && !loading && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--color-text-muted)', gap: 'var(--space-4)' }}>
                <div style={{ fontSize: '48px' }}>📝</div>
                <p>No summary generated yet.</p>
              </div>
            )}

            {loading && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 'var(--space-4)' }}>
                <div className="upload-spinner" style={{ width: '40px', height: '40px', border: '3px solid var(--color-border)', borderTopColor: 'var(--color-primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                <p style={{ color: 'var(--color-text-muted)' }}>Generating insights...</p>
              </div>
            )}

            {summary && (
              <div style={{ animation: 'fadeIn 0.3s ease' }}>
                <div style={{ 
                  lineHeight: 1.6, 
                  fontSize: 'var(--text-base)', 
                  whiteSpace: 'pre-wrap', 
                  marginBottom: 'var(--space-6)',
                  color: 'var(--color-text)'
                }}>
                  {summary.summary}
                </div>

                {summary.key_points && summary.key_points.length > 0 && (
                  <div style={{ background: 'var(--color-surface-alt)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                    <h4 style={{ fontSize: 'var(--text-xs)', fontWeight: 700, textTransform: 'uppercase', marginBottom: 'var(--space-3)', color: 'var(--color-primary)' }}>Key Takeaways</h4>
                    <ul style={{ paddingLeft: 'var(--space-4)', margin: 0 }}>
                      {summary.key_points.map((pt, i) => (
                        <li key={i} style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--text-sm)' }}>{pt}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>
    </div>
  );
}