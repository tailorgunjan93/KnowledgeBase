import React, { useState, useEffect } from 'react';
import { settingsAPI } from '../api';

export function SettingsPage({ user }) {
  const [groqApiKey, setGroqApiKey] = useState('');
  const [groqModel, setGroqModel] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await settingsAPI.get();
      if (res.data.groq_api_key) setGroqApiKey(res.data.groq_api_key);
      if (res.data.groq_model) setGroqModel(res.data.groq_model);
    } catch (err) {
      console.error('Failed to fetch settings');
    }
  };

  const saveSettings = async () => {
    try {
      await settingsAPI.update('groq_api_key', groqApiKey);
      if (groqModel) await settingsAPI.update('groq_model', groqModel);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to save settings');
    }
  };

  return (
    <div className="settings-page">
      <h1>Settings</h1>

      <div className="settings-content">
        <div className="setting-group">
          <h2>API Configuration</h2>
          <label>GROQ API Key</label>
          <input
            type="password"
            placeholder="Enter your Groq API key"
            value={groqApiKey}
            onChange={(e) => setGroqApiKey(e.target.value)}
          />
          <p className="help-text">
            Get your free API key from{' '}
            <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer">
              https://console.groq.com
            </a>
          </p>

          <label>Model</label>
          <select value={groqModel || 'openai/gpt-oss-120b'} onChange={(e) => setGroqModel(e.target.value)}>
            <option value="openai/gpt-oss-120b">GPT-OSS 120B</option>
          </select>

          <button onClick={saveSettings}>Save Settings</button>
          {saved && <span className="saved-message">Saved!</span>}
        </div>

        <div className="setting-group">
          <h2>Account</h2>
          <p><strong>Username:</strong> {user?.username}</p>
        </div>
      </div>
    </div>
  );
}