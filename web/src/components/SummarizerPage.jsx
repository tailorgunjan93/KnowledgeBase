import { useState } from 'react';
import { httpClient } from '../api/httpClient';

export function SummarizerPage() {
  const [text,    setText]    = useState('');
  const [file,    setFile]    = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const [copied,  setCopied]  = useState(false);

  const handleSummarize = async () => {
    if (!text.trim() && !file) return;
    setLoading(true); setError(''); setSummary(null);
    try {
      let res;
      if (file) {
        const fd = new FormData();
        fd.append('file', file);
        res = await httpClient.post('/api/summarize/file', fd);
      } else {
        res = await httpClient.post('/api/summarize', { text });
      }
      setSummary(res.data);
    } catch (err) {
      setError(err.message || 'Summarization failed');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!summary?.summary) return;
    navigator.clipboard.writeText(summary.summary).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const canSubmit = !loading && (text.trim() || file);

  return (
    <div className="summarizer-page">
      <div className="summarizer-header">
        <h1>Summarizer</h1>
        <p>Transform long documents into concise, actionable summaries using AI.</p>
      </div>

      <div className="summarizer-body">
        {/* ── Input panel ── */}
        <div className="summarizer-panel">
          <div className="summarizer-panel-title">Input</div>

          <textarea
            className="summarizer-textarea"
            placeholder="Paste your text here…"
            value={text}
            onChange={e => setText(e.target.value)}
            disabled={!!file || loading}
          />

          {/* File upload */}
          <div style={{
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--color-border)',
            background: 'var(--color-surface-alt)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-2)',
          }}>
            <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-muted)' }}>
              Or upload a file (PDF, DOCX, TXT)
            </span>
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt,.md"
              onChange={e => { setFile(e.target.files[0] || null); setText(''); }}
              disabled={loading}
              style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}
            />
            {file && (
              <button
                onClick={() => setFile(null)}
                style={{
                  alignSelf: 'flex-start', background: 'none', border: 'none',
                  color: 'var(--color-error)', cursor: 'pointer',
                  fontSize: 'var(--text-xs)', fontWeight: 600, padding: 0,
                }}
              >
                ✕ Remove {file.name}
              </button>
            )}
          </div>

          {error && (
            <div style={{
              color: 'var(--color-error-text)', background: 'var(--color-error-bg)',
              padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-xs)',
              fontSize: 'var(--text-xs)', border: '1px solid var(--color-error)',
            }}>
              {error}
            </div>
          )}

          <button
            className="btn-summarize"
            onClick={handleSummarize}
            disabled={!canSubmit}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                Generating…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
                Summarize
              </>
            )}
          </button>
        </div>

        {/* ── Output panel ── */}
        <div className="summarizer-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="summarizer-panel-title">Result</div>
            {summary && (
              <button className="btn-copy" onClick={copyToClipboard}>
                {copied ? '✓ Copied' : 'Copy text'}
              </button>
            )}
          </div>

          <div className="summarizer-result">
            {!summary && !loading && (
              <div className="summarizer-empty">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-faint)" strokeWidth="1.2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                <span>Summary will appear here</span>
              </div>
            )}

            {loading && (
              <div className="summarizer-empty">
                <div className="spinner" />
                <span style={{ color: 'var(--color-text-muted)' }}>Generating insights…</span>
              </div>
            )}

            {summary && (
              <div style={{ animation: 'fadeIn 0.3s ease' }}>
                <p style={{ fontSize: 'var(--text-base)', lineHeight: 1.85, whiteSpace: 'pre-wrap', marginBottom: 'var(--space-4)' }}>
                  {summary.summary}
                </p>

                {summary.key_points?.length > 0 && (
                  <div style={{
                    background: 'var(--color-primary-light)',
                    padding: 'var(--space-4)',
                    borderRadius: 'var(--radius-sm)',
                    borderLeft: '3px solid var(--color-primary)',
                  }}>
                    <div style={{
                      fontSize: 'var(--text-xs)', fontWeight: 700,
                      textTransform: 'uppercase', letterSpacing: '0.05em',
                      color: 'var(--color-primary)', marginBottom: 'var(--space-3)',
                    }}>
                      Key Takeaways
                    </div>
                    <ul style={{ paddingLeft: 'var(--space-5)', margin: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                      {summary.key_points.map((pt, i) => (
                        <li key={i} style={{ fontSize: 'var(--text-base)', lineHeight: 1.7 }}>{pt}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div style={{
                  marginTop: 'var(--space-4)', fontSize: 'var(--text-xs)',
                  color: 'var(--color-text-faint)',
                  borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-3)',
                }}>
                  {summary.original_length && `${summary.original_length.toLocaleString()} → ${summary.summary_length?.toLocaleString()} chars`}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
