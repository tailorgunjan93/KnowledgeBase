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
    setLoading(true);
    setError('');
    setSummary(null);

    try {
      let res;
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        res = await apiClient.post('/api/summarize/file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        res = await apiClient.post('/api/summarize', { text });
      }
      if (res.data.error) {
        setError(res.data.error);
      } else {
        setSummary(res.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Summarization failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="summarizer-page">
      <h1>Document Summarizer</h1>

      <div className="summarizer-content">
        <div className="input-section">
          <textarea
            placeholder="Paste your text here to summarize..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={!!file}
            rows={10}
          />
          <div className="file-upload">
            <span>Or upload a document: </span>
            <input type="file" onChange={(e) => setFile(e.target.files[0])} />
          </div>
          <button onClick={handleSummarize} disabled={loading || (!text.trim() && !file)}>
            {loading ? 'Summarizing...' : 'Summarize'}
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {summary && (
          <div className="summary-result">
            <h2>Summary</h2>
            <p className="summary-text">{summary.summary}</p>

            {summary.key_points && summary.key_points.length > 0 && (
              <div className="key-points">
                <h3>Key Points:</h3>
                <ul>
                  {summary.key_points.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="stats">
              <span>Original: {summary.original_length} chars</span>
              <span>Summary: {summary.summary_length} chars</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}