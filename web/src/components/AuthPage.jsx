import React, { useState, useEffect } from 'react';
import { authAPI } from '../api';

export function AuthPage({ onLogin }) {
  const [activeTab, setActiveTab] = useState('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('kbase-theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kbase-theme', theme);
  }, [theme]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = activeTab === 'login'
        ? await authAPI.login(username, password)
        : await authAPI.signup(username, email, password);
      onLogin(res.data.token);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail[0]?.msg || 'Validation failed');
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Authentication failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const switchTab = (tab) => {
    setActiveTab(tab);
    setError('');
    setUsername('');
    setEmail('');
    setPassword('');
  };

  const togglePw = () => setShowPw(!showPw);

  return (
    <div className="auth-body">
      <div className="stars">
        {[...Array(30)].map((_, i) => (
          <div key={i} className="star" style={{
            width: Math.random() * 2 + 1 + 'px',
            height: Math.random() * 2 + 1 + 'px',
            top: Math.random() * 100 + '%',
            left: Math.random() * 100 + '%',
            '--dur': (Math.random() * 3 + 2).toFixed(1) + 's',
            '--delay': '-' + (Math.random() * 4).toFixed(1) + 's'
          }} />
        ))}
      </div>

      <div className="theme-toggle-auth">
        <button className={`theme-btn ${theme === 'light' ? 'active' : ''}`} onClick={() => setTheme('light')}>☀️</button>
        <button className={`theme-btn ${theme === 'dark' ? 'active' : ''}`} onClick={() => setTheme('dark')}>🌙</button>
      </div>

      <div className="card">
        <div className="logo">
          <div className="logo-mark">
            <svg viewBox="0 0 26 26" fill="none">
              <path d="M6 4L6 22" stroke="var(--btn-text)" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M6 13L16 5" stroke="var(--btn-text)" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M6 13L18 21" stroke="var(--btn-text)" strokeWidth="2.5" strokeLinecap="round"/>
              <circle cx="20" cy="5" r="2.5" fill="var(--accent)"/>
            </svg>
          </div>
          <span className="logo-name">KBase</span>
        </div>

        <div className="tabs">
          <button className={`tab-btn ${activeTab === 'login' ? 'active' : ''}`} onClick={() => switchTab('login')}>Sign In</button>
          <button className={`tab-btn ${activeTab === 'signup' ? 'active' : ''}`} onClick={() => switchTab('signup')}>Create Account</button>
        </div>

        {activeTab === 'login' ? (
          <div className="panel active">
            <p className="heading">Welcome back.</p>
            <p className="subheading">Sign in to your knowledge base</p>
            <form onSubmit={handleSubmit}>
              <div className="field-group">
                <label className="field-label">Username</label>
                <div className="field-wrap">
                  <span className="field-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="2" y="4" width="20" height="16" rx="3"/><path d="m2 7 10 7 10-7"/></svg>
                  </span>
                  <input className="field-input" type="text" placeholder="Your username" value={username} onChange={e => setUsername(e.target.value)} required />
                </div>
              </div>
              <div className="field-group">
                <label className="field-label">Password</label>
                <div className="field-wrap">
                  <span className="field-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  </span>
                  <input className="field-input" type={showPw ? 'text' : 'password'} placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required />
                  <button type="button" className="toggle-pw" onClick={togglePw}>
                    {showPw ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                    )}
                  </button>
                </div>
              </div>
              <div className="forgot-row"><a href="#" className="link">Forgot password?</a></div>
              {error && <div className="error-message">{error}</div>}
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Signing In...' : 'Sign In'}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </form>
            <div className="divider">
              <span className="divider-line"></span><span className="divider-text">or continue with</span><span className="divider-line"></span>
            </div>
            <button type="button" className="btn-oauth">
              <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Continue with Google
            </button>
            <p className="card-footer">Don't have an account? <a href="#" className="link" onClick={(e) => { e.preventDefault(); switchTab('signup'); }}>Sign Up</a></p>
          </div>
        ) : (
          <div className="panel active">
            <p className="heading">Join KBase.</p>
            <p className="subheading">Create your free account today</p>
            <form onSubmit={handleSubmit}>
              <div className="field-group">
                <label className="field-label">Username</label>
                <div className="field-wrap">
                  <span className="field-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg></span>
                  <input className="field-input" type="text" placeholder="Alex" value={username} onChange={e => setUsername(e.target.value)} required />
                </div>
              </div>
              <div className="field-group">
                <label className="field-label">Email</label>
                <div className="field-wrap">
                  <span className="field-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="2" y="4" width="20" height="16" rx="3"/><path d="m2 7 10 7 10-7"/></svg></span>
                  <input className="field-input" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} />
                </div>
              </div>
              <div className="field-group">
                <label className="field-label">Password</label>
                <div className="field-wrap">
                  <span className="field-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></span>
                  <input className="field-input" type={showPw ? 'text' : 'password'} placeholder="Min. 8 characters" value={password} onChange={e => setPassword(e.target.value)} required />
                  <button type="button" className="toggle-pw" onClick={togglePw}>
                    {showPw ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                    )}
                  </button>
                </div>
              </div>
              <p className="terms-note" style={{marginTop: '-12px', marginBottom: '20px'}}>
                By signing up, you agree to our <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>
              </p>
              {error && <div className="error-message">{error}</div>}
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Creating...' : 'Create Account'}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </form>
            <div className="divider">
              <span className="divider-line"></span><span className="divider-text">or</span><span className="divider-line"></span>
            </div>
            <button type="button" className="btn-oauth">
              <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Sign up with Google
            </button>
            <p className="card-footer">Already have an account? <a href="#" className="link" onClick={(e) => { e.preventDefault(); switchTab('login'); }}>Sign In</a></p>
          </div>
        )}
      </div>
    </div>
  );
}