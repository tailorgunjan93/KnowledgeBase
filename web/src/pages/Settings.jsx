import React, { useState, useEffect } from 'react';
import * as settingsAPI from '../api/settingsApi';

export function SettingsPage({ user }) {
  const [groqApiKey, setGroqApiKey] = useState('');
  const [groqModel, setGroqModel] = useState('');
  const [saved, setSaved] = useState(false);
  const [provider, setProvider] = useState(null);

  useEffect(() => { fetchSettings(); fetchProvider(); }, []);

  const fetchSettings = async () => {
    try {
      const res = await settingsAPI.get();
      if (res.data.groq_api_key) setGroqApiKey(res.data.groq_api_key);
      if (res.data.groq_model) setGroqModel(res.data.groq_model);
    } catch (err) { console.error('Failed to fetch settings'); }
  };

  const fetchProvider = async () => {
    try {
      const res = await settingsAPI.getLLMProvider();
      setProvider(res.data);
    } catch (err) { console.error('Failed to fetch provider info'); }
  };

  const saveSettings = async () => {
    try {
      await settingsAPI.update('groq_api_key', groqApiKey);
      if (groqModel) await settingsAPI.update('groq_model', groqModel);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      fetchProvider();
    } catch (err) { console.error('Failed to save settings'); }
  };

  const activeProvider = provider?.active_provider || 'none';

  return (
    <div style={{padding: '32px 40px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '24px'}}>
      <h2 style={{fontFamily: 'Fraunces, serif', fontSize: '24px', fontWeight: 400, color: 'var(--ink)'}}>Settings</h2>
      
      <div style={{maxWidth: '600px', display: 'flex', flexDirection: 'column', gap: '16px'}}>
        <div style={{background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px'}}>
          <h2 style={{fontSize: '16px', fontWeight: 500, color: 'var(--ink)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px'}}>
            🤖 LLM Provider Status
          </h2>
          
          <div style={{display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px', borderRadius: '10px', background: 'var(--bg)', fontSize: '13px', marginBottom: '12px', border: '1px solid var(--border)'}}>
            <span style={{width: '8px', height: '8px', borderRadius: '50%', background: activeProvider !== 'none' ? 'var(--green)' : 'var(--red)', boxShadow: activeProvider !== 'none' ? '0 0 6px var(--green)' : 'none'}} />
            <strong style={{color: 'var(--ink)'}}>Active: {activeProvider === 'groq' ? 'Groq Cloud' : activeProvider === 'ollama' ? 'Ollama (Local)' : 'No Provider'}</strong>
          </div>

          {provider?.ollama && (
            <div style={{display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px', borderRadius: '10px', background: 'var(--bg)', fontSize: '13px', marginBottom: '12px', border: '1px solid var(--border)'}}>
              <span style={{width: '8px', height: '8px', borderRadius: '50%', background: provider.ollama.available ? 'var(--green)' : 'var(--red)'}} />
              <span style={{color: 'var(--ink2)'}}>Ollama: {provider.ollama.available ? `Running (${provider.ollama.model})` : 'Not running'}</span>
            </div>
          )}
        </div>

        <div style={{background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px'}}>
          <h2 style={{fontSize: '16px', fontWeight: 500, color: 'var(--ink)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px'}}>
            ☁️ Groq Configuration
          </h2>
          
          <p style={{fontSize: '13px', color: 'var(--ink3)', marginBottom: '16px', lineHeight: 1.5}}>
            To use Groq's extremely fast free-tier API, enter your API key below. If no key is provided, the system will fall back to local Ollama.
          </p>
          
          <div style={{marginBottom: '16px'}}>
            <label style={{display: 'block', marginBottom: '8px', fontSize: '12px', fontWeight: 500, color: 'var(--ink2)', textTransform: 'uppercase', letterSpacing: '0.5px'}}>Groq API Key</label>
            <input 
              type="password" 
              value={groqApiKey} 
              onChange={e => setGroqApiKey(e.target.value)}
              placeholder="gsk_..."
              style={{width: '100%', padding: '12px 14px', border: '1px solid var(--border)', borderRadius: '10px', background: 'var(--bg)', color: 'var(--ink)', fontSize: '14px', outline: 'none', fontFamily: 'inherit'}}
            />
          </div>

          <div style={{marginBottom: '20px'}}>
            <label style={{display: 'block', marginBottom: '8px', fontSize: '12px', fontWeight: 500, color: 'var(--ink2)', textTransform: 'uppercase', letterSpacing: '0.5px'}}>Preferred Model</label>
            <select 
              value={groqModel} 
              onChange={e => setGroqModel(e.target.value)}
              style={{width: '100%', padding: '12px 14px', border: '1px solid var(--border)', borderRadius: '10px', background: 'var(--bg)', color: 'var(--ink)', fontSize: '14px', outline: 'none', fontFamily: 'inherit', appearance: 'none'}}
            >
              <option value="">Default (llama3-70b-8192)</option>
              <option value="llama3-70b-8192">LLaMA3 70B</option>
              <option value="llama3-8b-8192">LLaMA3 8B</option>
              <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
              <option value="gpt-oss-120b">GPT OSS 120B</option>
            </select>
          </div>

          <div style={{display: 'flex', alignItems: 'center'}}>
            <button onClick={saveSettings} style={{padding: '12px 24px', background: 'var(--amber)', color: 'var(--bg)', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '14px', fontWeight: 600, fontFamily: 'inherit'}}>
              Save Settings
            </button>
            {saved && <span style={{marginLeft: '12px', color: 'var(--green)', fontSize: '13px', fontWeight: 500}}>Saved successfully!</span>}
          </div>
        </div>
      </div>
    </div>
  );
}