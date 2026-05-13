import { useState, useEffect, useCallback } from 'react';
import * as settingsAPI from '../api/settingsApi';

const PROVIDERS = ['groq', 'openai', 'gemini', 'nvidia', 'aws', 'ollama'];

const PROVIDER_LABELS = {
  groq:   'Groq',
  openai: 'OpenAI',
  gemini: 'Gemini',
  nvidia: 'NVIDIA',
  aws:    'AWS Bedrock',
  ollama: 'Ollama',
};

const STATIC_MODELS = {
  groq: [
    { id: 'llama-3.1-8b-instant',    label: 'LLaMA 3.1 8B Instant (fast)' },
    { id: 'llama-3.1-70b-versatile', label: 'LLaMA 3.1 70B Versatile' },
    { id: 'llama3-8b-8192',          label: 'LLaMA 3 8B' },
    { id: 'llama3-70b-8192',         label: 'LLaMA 3 70B' },
    { id: 'gemma2-9b-it',            label: 'Gemma 2 9B' },
  ],
  openai: [
    { id: 'gpt-4o',      label: 'GPT-4o' },
    { id: 'gpt-4o-mini', label: 'GPT-4o Mini (fast)' },
    { id: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { id: 'o1-mini',     label: 'o1 Mini (reasoning)' },
  ],
  gemini: [
    { id: 'gemini-2.0-flash',    label: 'Gemini 2.0 Flash' },
    { id: 'gemini-1.5-pro',      label: 'Gemini 1.5 Pro (1M context)' },
    { id: 'gemini-1.5-flash',    label: 'Gemini 1.5 Flash' },
    { id: 'gemini-1.5-flash-8b', label: 'Gemini 1.5 Flash 8B (fast)' },
  ],
  nvidia: [
    { id: 'meta/llama-3.1-8b-instruct',             label: 'Meta Llama 3.1 8B' },
    { id: 'meta/llama-3.1-70b-instruct',            label: 'Meta Llama 3.1 70B' },
    { id: 'meta/llama-3.3-70b-instruct',            label: 'Meta Llama 3.3 70B' },
    { id: 'nvidia/llama-3.1-nemotron-70b-instruct', label: 'NVIDIA Nemotron 70B' },
    { id: 'mistralai/mistral-7b-instruct-v0.3',     label: 'Mistral 7B' },
    { id: 'microsoft/phi-3-mini-128k-instruct',     label: 'Phi-3 Mini 128K' },
  ],
  aws: [
    { id: 'anthropic.claude-3-5-sonnet-20241022-v2:0', label: 'Claude 3.5 Sonnet' },
    { id: 'anthropic.claude-3-haiku-20240307-v1:0',    label: 'Claude 3 Haiku (fast)' },
    { id: 'amazon.nova-lite-v1:0',                     label: 'Amazon Nova Lite' },
    { id: 'meta.llama3-8b-instruct-v1:0',              label: 'Llama 3 8B' },
    { id: 'meta.llama3-70b-instruct-v1:0',             label: 'Llama 3 70B' },
    { id: 'mistral.mistral-7b-instruct-v0:2',          label: 'Mistral 7B' },
  ],
};

const AWS_REGIONS = [
  'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1',
  'ap-southeast-1', 'ap-northeast-1', 'ap-south-1',
];

const DEFAULT_CFG = {
  active_provider: 'groq',
  groq_api_key: '', groq_model: '',
  openai_api_key: '', openai_model: '',
  gemini_api_key: '', gemini_model: '',
  nvidia_api_key: '', nvidia_model: '',
  aws_access_key_id: '', aws_secret_access_key: '', aws_region: 'us-east-1', aws_model: '',
  ollama_model: '',
};

export function SettingsPage({ user }) {
  const [activeTab, setActiveTab]           = useState('groq');
  const [cfg, setCfg]                       = useState(DEFAULT_CFG);
  const [provider, setProvider]             = useState(null);
  const [models, setModels]                 = useState([]);
  const [modelsSource, setModelsSource]     = useState('');
  const [modelsFetching, setModelsFetching] = useState(false);
  const [showKeys, setShowKeys]             = useState({});
  const [saved, setSaved]                   = useState(false);
  const [saving, setSaving]                 = useState(false);
  const [useCustomModel, setUseCustomModel] = useState(false);

  useEffect(() => { fetchSettings(); fetchProvider(); }, []);

  const fetchSettings = async () => {
    try {
      const res = await settingsAPI.get();
      const d = res.data || {};
      const merged = { ...DEFAULT_CFG };
      for (const k of Object.keys(DEFAULT_CFG)) {
        if (d[k] !== undefined && d[k] !== null && d[k] !== '') merged[k] = d[k];
      }
      setCfg(merged);
      const tab = merged.active_provider || 'groq';
      setActiveTab(tab);
      loadModelsFor(tab, merged[`${tab}_api_key`] || '');
    } catch { /* silent */ }
  };

  const fetchProvider = async () => {
    try {
      const res = await settingsAPI.getLLMProvider();
      setProvider(res.data);
    } catch { /* silent */ }
  };

  const loadModelsFor = useCallback(async (p, key) => {
    if (p === 'ollama') { setModels([]); setModelsSource('ollama'); return; }

    setModelsFetching(true);
    try {
      const res = await settingsAPI.fetchModels(p, key || '');
      if (res.data?.models?.length) {
        setModels(res.data.models);
        setModelsSource(res.data.source || p);
      } else {
        setModels(STATIC_MODELS[p] || []);
        setModelsSource('fallback');
      }
    } catch {
      setModels(STATIC_MODELS[p] || []);
      setModelsSource('fallback');
    } finally {
      setModelsFetching(false);
    }
  }, []);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setModels([]);
    setModelsSource('');
    setUseCustomModel(false);
    loadModelsFor(tab, cfg[`${tab}_api_key`] || '');
  };

  const set = (key, val) => setCfg(prev => ({ ...prev, [key]: val }));

  const saveProvider = async () => {
    setSaving(true);
    const keysByProvider = {
      groq:   ['groq_api_key', 'groq_model'],
      openai: ['openai_api_key', 'openai_model'],
      gemini: ['gemini_api_key', 'gemini_model'],
      nvidia: ['nvidia_api_key', 'nvidia_model'],
      aws:    ['aws_access_key_id', 'aws_secret_access_key', 'aws_region', 'aws_model'],
      ollama: ['ollama_model'],
    };
    const updates = { active_provider: activeTab };
    for (const k of (keysByProvider[activeTab] || [])) updates[k] = cfg[k] || '';
    try {
      await Promise.all(Object.entries(updates).map(([k, v]) => settingsAPI.update(k, v)));
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      fetchProvider();
    } catch { /* silent */ } finally {
      setSaving(false);
    }
  };

  const toggleKey = (k) => setShowKeys(p => ({ ...p, [k]: !p[k] }));

  /* ── Shared sub-components ───────────────────────────────── */
  const KeyInput = ({ field, placeholder }) => (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      <input
        type={showKeys[field] ? 'text' : 'password'}
        value={cfg[field] || ''}
        onChange={e => set(field, e.target.value)}
        placeholder={placeholder || ''}
        style={{ paddingRight: 42 }}
      />
      <button type="button" onClick={() => toggleKey(field)} style={{
        position: 'absolute', right: 12, background: 'none', border: 'none',
        cursor: 'pointer', color: 'var(--color-text-faint)', display: 'flex', alignItems: 'center',
      }}>
        {showKeys[field]
          ? <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          : <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
        }
      </button>
    </div>
  );

  const ModelSelect = ({ field }) => {
    const currentVal = cfg[field] || '';
    const inList = !currentVal || models.some(m => m.id === currentVal);
    const showCustom = useCustomModel || (currentVal !== '' && models.length > 0 && !inList);

    if (showCustom) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <input
            type="text"
            value={currentVal}
            onChange={e => set(field, e.target.value)}
            placeholder="e.g. gpt-4o, gemini-2.0-pro-exp…"
            autoFocus
          />
          {models.length > 0 && (
            <button type="button" onClick={() => { setUseCustomModel(false); set(field, ''); }}
              style={{ alignSelf: 'flex-start', background: 'none', border: 'none',
                fontSize: 'var(--text-xs)', color: 'var(--color-primary)', cursor: 'pointer', padding: 0 }}>
              ← Pick from list
            </button>
          )}
        </div>
      );
    }

    return (
      <div style={{ position: 'relative' }}>
        <select
          value={currentVal}
          onChange={e => {
            if (e.target.value === '__custom__') {
              setUseCustomModel(true);
              set(field, '');
            } else {
              set(field, e.target.value);
            }
          }}
          disabled={modelsFetching}
        >
          <option value="">Default</option>
          {models.map(m => <option key={m.id} value={m.id}>{m.label || m.id}</option>)}
          <option value="__custom__">— Enter custom model ID…</option>
        </select>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-faint)" strokeWidth="2"
          style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}>
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
    );
  };

  const RefreshBtn = () => (
    <button onClick={() => loadModelsFor(activeTab, cfg[`${activeTab}_api_key`] || '')}
      disabled={modelsFetching} style={{
        display: 'flex', alignItems: 'center', gap: 4,
        background: 'none', border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-xs)', padding: '3px 10px',
        fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)',
        cursor: modelsFetching ? 'not-allowed' : 'pointer', opacity: modelsFetching ? 0.6 : 1,
      }}>
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
        style={{ animation: modelsFetching ? 'spin 1s linear infinite' : 'none' }}>
        <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
      </svg>
      {modelsFetching ? 'Fetching…' : 'Refresh'}
    </button>
  );

  const ModelRow = ({ field }) => (
    <div className="settings-field">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
        <label style={{ marginBottom: 0 }}>Model</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          {modelsSource && modelsSource !== 'fallback' && modelsSource !== 'ollama' && (
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-success)', background: 'var(--color-success-bg)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', fontWeight: 600 }}>
              Live
            </span>
          )}
          {activeTab !== 'ollama' && <RefreshBtn />}
        </div>
      </div>
      <ModelSelect field={field} />
    </div>
  );

  const isActive = provider?.active_provider === activeTab;

  /* ── Render ──────────────────────────────────────────────── */
  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Configure your LLM provider and application preferences.</p>
      </div>

      <div className="settings-body">

        {/* Status card */}
        <div className="settings-card">
          <div className="settings-card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            LLM Provider Status
          </div>
          <div className="provider-status-row">
            <span style={{
              width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
              background: provider?.active_provider && provider.active_provider !== 'none'
                ? 'var(--color-success)' : 'var(--color-error)',
              boxShadow: provider?.active_provider && provider.active_provider !== 'none'
                ? '0 0 6px var(--color-success)' : 'none',
            }}/>
            <strong style={{ color: 'var(--color-text)', fontSize: 'var(--text-sm)' }}>
              Active:{' '}
              {provider?.active_provider && provider.active_provider !== 'none'
                ? (PROVIDER_LABELS[provider.active_provider] || provider.active_provider)
                : 'No Provider — configure one below'}
            </strong>
          </div>
        </div>

        {/* Config card */}
        <div className="settings-card">
          <div className="settings-card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            LLM Configuration
          </div>

          {/* Provider tab bar */}
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 'var(--space-5)',
            borderBottom: '1px solid var(--color-border)', paddingBottom: 'var(--space-3)' }}>
            {PROVIDERS.map(p => (
              <button key={p} onClick={() => handleTabChange(p)} style={{
                padding: '5px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid',
                borderColor: activeTab === p ? 'var(--color-primary)' : 'var(--color-border)',
                background: activeTab === p ? 'var(--color-primary-light)' : 'transparent',
                color: activeTab === p ? 'var(--color-primary)' : 'var(--color-text-muted)',
                fontWeight: activeTab === p ? 600 : 400,
                fontSize: 'var(--text-sm)', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {PROVIDER_LABELS[p]}
                {provider?.active_provider === p && (
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-success)', display: 'inline-block' }}/>
                )}
              </button>
            ))}
          </div>

          {/* ── Groq ── */}
          {activeTab === 'groq' && <>
            <p className="settings-field-hint" style={{ marginBottom: 'var(--space-4)' }}>
              Fast free-tier inference. Get a key at{' '}
              <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)' }}>console.groq.com</a>
            </p>
            <div className="settings-field"><label>API Key</label><KeyInput field="groq_api_key" placeholder="gsk_..." /></div>
            <ModelRow field="groq_model" />
          </>}

          {/* ── OpenAI ── */}
          {activeTab === 'openai' && <>
            <p className="settings-field-hint" style={{ marginBottom: 'var(--space-4)' }}>
              GPT-4o and o1 models. Get a key at{' '}
              <a href="https://platform.openai.com" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)' }}>platform.openai.com</a>
            </p>
            <div className="settings-field"><label>API Key</label><KeyInput field="openai_api_key" placeholder="sk-..." /></div>
            <ModelRow field="openai_model" />
          </>}

          {/* ── Gemini ── */}
          {activeTab === 'gemini' && <>
            <p className="settings-field-hint" style={{ marginBottom: 'var(--space-4)' }}>
              Google Gemini — up to 1M token context. Get a key at{' '}
              <a href="https://aistudio.google.com" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)' }}>aistudio.google.com</a>
            </p>
            <div className="settings-field"><label>API Key</label><KeyInput field="gemini_api_key" placeholder="AIza..." /></div>
            <ModelRow field="gemini_model" />
          </>}

          {/* ── NVIDIA ── */}
          {activeTab === 'nvidia' && <>
            <p className="settings-field-hint" style={{ marginBottom: 'var(--space-4)' }}>
              NVIDIA NIM — hosted open-source models. Get a key at{' '}
              <a href="https://build.nvidia.com" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)' }}>build.nvidia.com</a>
            </p>
            <div className="settings-field"><label>API Key</label><KeyInput field="nvidia_api_key" placeholder="nvapi-..." /></div>
            <ModelRow field="nvidia_model" />
          </>}

          {/* ── AWS ── */}
          {activeTab === 'aws' && <>
            <p className="settings-field-hint" style={{ marginBottom: 'var(--space-4)' }}>
              AWS Bedrock — Claude, Llama, Mistral and more. Requires an IAM user with Bedrock invoke permissions.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
              <div className="settings-field">
                <label>Access Key ID</label>
                <input type="text" value={cfg.aws_access_key_id || ''} onChange={e => set('aws_access_key_id', e.target.value)} placeholder="AKIA..." />
              </div>
              <div className="settings-field">
                <label>Secret Access Key</label>
                <KeyInput field="aws_secret_access_key" placeholder="Secret key" />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
              <div className="settings-field">
                <label>Region</label>
                <div style={{ position: 'relative' }}>
                  <select value={cfg.aws_region || 'us-east-1'} onChange={e => set('aws_region', e.target.value)}>
                    {AWS_REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-faint)" strokeWidth="2"
                    style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}>
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </div>
              </div>
              <div className="settings-field">
                <label>Model</label>
                <ModelSelect field="aws_model" />
              </div>
            </div>
          </>}

          {/* ── Ollama ── */}
          {activeTab === 'ollama' && <>
            <p className="settings-field-hint" style={{ marginBottom: 'var(--space-4)' }}>
              Local Ollama server — no API key needed. Install from{' '}
              <a href="https://ollama.com" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)' }}>ollama.com</a>{' '}
              then run <code style={{ background: 'var(--color-surface-alt)', padding: '1px 6px', borderRadius: 4, fontSize: '0.9em' }}>ollama pull llama3.1:8b</code>
            </p>
            <div className="settings-field">
              <label>Model name</label>
              <input type="text" value={cfg.ollama_model || ''} onChange={e => set('ollama_model', e.target.value)} placeholder="llama3.1:8b" />
            </div>
          </>}

          <div className="settings-save-row" style={{ marginTop: 'var(--space-5)' }}>
            <button className="btn-settings-save" onClick={saveProvider} disabled={saving || saved}>
              {saving ? 'Saving…' : saved ? '✓ Saved & Activated' : `Save & Activate ${PROVIDER_LABELS[activeTab]}`}
            </button>
            {isActive && !saved && (
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-success)', fontWeight: 600 }}>
                ✓ Currently active
              </span>
            )}
          </div>
        </div>

        {/* Account */}
        <div className="settings-card">
          <div className="settings-card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
            Account
          </div>
          <div className="provider-status-row">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-faint)" strokeWidth="2">
              <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
            </svg>
            <span style={{ color: 'var(--color-text)', fontSize: 'var(--text-sm)', fontWeight: 500 }}>{user?.username || '—'}</span>
            {user?.email && <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>· {user.email}</span>}
          </div>
        </div>

      </div>
    </div>
  );
}
