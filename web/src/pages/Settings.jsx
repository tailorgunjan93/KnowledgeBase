import { useState, useEffect, useCallback } from 'react';
import * as settingsAPI from '../api/settingsApi';

const FALLBACK_MODELS = [
  { id: 'llama-3.1-8b-instant',    label: 'LLaMA 3.1 — 8B Instant (fast)' },
  { id: 'llama-3.1-70b-versatile', label: 'LLaMA 3.1 — 70B Versatile' },
  { id: 'llama3-8b-8192',          label: 'LLaMA 3 — 8B' },
  { id: 'llama3-70b-8192',         label: 'LLaMA 3 — 70B' },
  { id: 'gemma2-9b-it',            label: 'Gemma 2 — 9B' },
  { id: 'gemma-7b-it',             label: 'Gemma — 7B' },
];

export function SettingsPage({ user }) {
  const [groqApiKey,    setGroqApiKey]    = useState('');
  const [groqModel,     setGroqModel]     = useState('');
  const [saved,         setSaved]         = useState(false);
  const [provider,      setProvider]      = useState(null);
  const [showKey,       setShowKey]       = useState(false);
  const [models,        setModels]        = useState(FALLBACK_MODELS);
  const [modelsSource,  setModelsSource]  = useState('fallback');
  const [modelsFetching, setModelsFetching] = useState(false);
  const [modelsError,   setModelsError]   = useState('');

  useEffect(() => { fetchSettings(); fetchProvider(); }, []);

  const fetchSettings = async () => {
    try {
      const res = await settingsAPI.get();
      const key   = res.data.groq_api_key || '';
      const model = res.data.groq_model   || '';
      setGroqApiKey(key);
      setGroqModel(model);
      if (key) loadModels(key);
    } catch { /* silent */ }
  };

  const fetchProvider = async () => {
    try {
      const res = await settingsAPI.getLLMProvider();
      setProvider(res.data);
    } catch { /* silent */ }
  };

  const loadModels = useCallback(async (keyOverride) => {
    setModelsFetching(true);
    setModelsError('');
    try {
      const res = await settingsAPI.fetchModels(keyOverride ?? groqApiKey);
      if (res.data?.models?.length) {
        setModels(res.data.models);
        setModelsSource(res.data.source || 'groq');
      } else {
        setModels(FALLBACK_MODELS);
        setModelsSource('fallback');
      }
    } catch {
      setModelsError('Could not fetch models — showing cached list.');
      setModels(FALLBACK_MODELS);
      setModelsSource('fallback');
    } finally {
      setModelsFetching(false);
    }
  }, [groqApiKey]);

  const saveSettings = async () => {
    try {
      await settingsAPI.update('groq_api_key', groqApiKey);
      await settingsAPI.update('groq_model', groqModel);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      fetchProvider();
      loadModels();
    } catch { /* silent */ }
  };

  const activeProvider = provider?.active_provider || 'none';
  const isOnline       = activeProvider !== 'none';

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Configure your LLM provider and application preferences.</p>
      </div>

      <div className="settings-body">
        {/* Provider Status */}
        <div className="settings-card">
          <div className="settings-card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            LLM Provider Status
          </div>

          <div className="provider-status-row">
            <span style={{
              width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
              background: isOnline ? 'var(--color-success)' : 'var(--color-error)',
              boxShadow: isOnline ? '0 0 6px var(--color-success)' : 'none',
            }}/>
            <strong style={{ color: 'var(--color-text)', fontSize: 'var(--text-sm)' }}>
              Active:{' '}
              {activeProvider === 'groq'   ? 'Groq Cloud' :
               activeProvider === 'ollama' ? 'Ollama (Local)' : 'No Provider'}
            </strong>
          </div>

          {provider?.ollama && (
            <div className="provider-status-row" style={{ marginTop: 'var(--space-2)' }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                background: provider.ollama.available ? 'var(--color-success)' : 'var(--color-text-faint)',
              }}/>
              <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>
                Ollama: {provider.ollama.available
                  ? `Running — ${provider.ollama.model}`
                  : 'Not running'}
              </span>
            </div>
          )}
        </div>

        {/* Groq Config */}
        <div className="settings-card">
          <div className="settings-card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            Groq Configuration
          </div>

          <p className="settings-field-hint" style={{ marginBottom: 'var(--space-4)' }}>
            Groq provides extremely fast, free-tier LLM inference. Enter your API key to enable it.
            Without a key, the system falls back to local Ollama.
          </p>

          {/* API Key */}
          <div className="settings-field">
            <label>Groq API Key</label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type={showKey ? 'text' : 'password'}
                value={groqApiKey}
                onChange={e => setGroqApiKey(e.target.value)}
                placeholder="gsk_..."
                style={{ paddingRight: '42px', fontFamily: groqApiKey && !showKey ? 'monospace' : 'inherit' }}
              />
              <button
                type="button"
                onClick={() => setShowKey(p => !p)}
                style={{
                  position: 'absolute', right: 12,
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--color-text-faint)', display: 'flex', alignItems: 'center',
                }}
              >
                {showKey ? (
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                ) : (
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                )}
              </button>
            </div>
            <p className="settings-field-hint">
              Get a free key at{' '}
              <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer"
                 style={{ color: 'var(--color-primary)', textDecoration: 'none', fontWeight: 500 }}>
                console.groq.com
              </a>
            </p>
          </div>

          {/* Model selector */}
          <div className="settings-field">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <label style={{ marginBottom: 0 }}>Preferred Model</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                {modelsSource === 'groq' && (
                  <span style={{
                    fontSize: 'var(--text-xs)', color: 'var(--color-success)',
                    background: 'var(--color-success-bg)', padding: '2px 8px',
                    borderRadius: 'var(--radius-xs)', fontWeight: 600,
                  }}>
                    Live from Groq
                  </span>
                )}
                {modelsSource === 'fallback' && (
                  <span style={{
                    fontSize: 'var(--text-xs)', color: 'var(--color-text-faint)',
                    background: 'var(--color-surface-alt)', padding: '2px 8px',
                    borderRadius: 'var(--radius-xs)',
                  }}>
                    Cached list
                  </span>
                )}
                <button
                  onClick={() => loadModels()}
                  disabled={modelsFetching}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 4,
                    background: 'none', border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-xs)', padding: '3px 10px',
                    fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)',
                    cursor: modelsFetching ? 'not-allowed' : 'pointer',
                    opacity: modelsFetching ? 0.6 : 1,
                  }}
                >
                  <svg
                    width="11" height="11" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5"
                    style={{ animation: modelsFetching ? 'spin 1s linear infinite' : 'none' }}
                  >
                    <polyline points="23 4 23 10 17 10"/>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                  </svg>
                  {modelsFetching ? 'Fetching…' : 'Refresh'}
                </button>
              </div>
            </div>

            <div style={{ position: 'relative' }}>
              <select
                value={groqModel}
                onChange={e => setGroqModel(e.target.value)}
                disabled={modelsFetching}
              >
                <option value="">Default (llama-3.1-8b-instant)</option>
                {models.map(m => (
                  <option key={m.id} value={m.id}>{m.label || m.id}</option>
                ))}
              </select>
              <svg
                width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="var(--color-text-faint)" strokeWidth="2"
                style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </div>

            {modelsError && (
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-error-text)', marginTop: 'var(--space-1)' }}>
                {modelsError}
              </p>
            )}
          </div>

          <div className="settings-save-row">
            <button className="btn-settings-save" onClick={saveSettings} disabled={saved}>
              {saved ? 'Saving...' : 'Save Settings'}
            </button>
            {saved && (
              <span className="save-success">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
                     style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }}>
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Saved!
              </span>
            )}
          </div>
        </div>

        {/* Account */}
        <div className="settings-card">
          <div className="settings-card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            Account
          </div>
          <div className="provider-status-row">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-faint)" strokeWidth="2">
              <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
            </svg>
            <span style={{ color: 'var(--color-text)', fontSize: 'var(--text-sm)', fontWeight: 500 }}>
              {user?.username || '—'}
            </span>
            {user?.email && (
              <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
                · {user.email}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
