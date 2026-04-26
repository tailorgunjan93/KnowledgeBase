import React, { useState, useEffect } from 'react';
import { kbAPI } from '../api';

export function ChatSidebar({ sessions, currentSession, onSelectSession, onNewChat }) {
  return (
    <div className="chat-sidebar">
      <button className="new-chat-btn" onClick={onNewChat}>+ New Chat</button>
      <div className="sessions-list">
        {sessions.map(s => (
          <div
            key={s.id}
            className={`session-item ${s.id === currentSession ? 'active' : ''}`}
            onClick={() => onSelectSession(s.id)}
          >
            {s.title}
          </div>
        ))}
      </div>
    </div>
  );
}

export function ChatOptions({ knowledgeBases, selectedKB, setSelectedKB, useWebSearch, setUseWebSearch }) {
  return (
    <div className="chat-options">
      <select
        value={selectedKB || ''}
        onChange={(e) => setSelectedKB(e.target.value ? Number(e.target.value) : null)}
      >
        <option value="">Select Knowledge Base (optional)</option>
        {knowledgeBases.map(kb => (
          <option key={kb.id} value={kb.id}>{kb.name}</option>
        ))}
      </select>
      <label className="web-search-toggle">
        <input
          type="checkbox"
          checked={useWebSearch}
          onChange={(e) => setUseWebSearch(e.target.checked)}
        />
        Enable Web Search
      </label>
    </div>
  );
}

export function ChatMessages({ messages, loading }) {
  return (
    <div className="messages-container">
      {messages.map((msg, idx) => (
        <div key={idx} className={`message ${msg.role}`}>
          <div className="message-content">{msg.content}</div>
          {msg.sources && msg.sources.length > 0 && (
            <div className="sources">
              <strong>Sources:</strong>
              {msg.sources.map((s, i) => (
                <div key={i} className="source-item">{s.text?.substring(0, 150)}...</div>
              ))}
            </div>
          )}
          {msg.confidence && (
            <div className="confidence">Confidence: {Math.round(msg.confidence * 100)}%</div>
          )}
        </div>
      ))}
      {loading && <div className="message assistant"><div className="loading">Thinking...</div></div>}
    </div>
  );
}

export function ChatInput({ message, setMessage, onSend, loading }) {
  return (
    <div className="chat-input">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && onSend()}
        placeholder="Ask a question..."
        disabled={loading}
      />
      <button onClick={onSend} disabled={loading || !message.trim()}>Send</button>
    </div>
  );
}

export function ChatPage({ user }) {
  const [message, setMessage] = useState('');
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKB, setSelectedKB] = useState(null);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSessions();
    fetchKnowledgeBases();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await kbAPI.list(0, 100);
      // Get sessions from chat API
      const { chatAPI } = await import('../api/chat');
      const sessRes = await chatAPI.getSessions();
      setSessions(sessRes.data);
    } catch (err) {
      console.error('Failed to fetch sessions');
    }
  };

  const fetchKnowledgeBases = async () => {
    try {
      const res = await kbAPI.list();
      setKnowledgeBases(res.data.items || []);
    } catch (err) {
      console.error('Failed to fetch KBs');
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const { chatAPI } = await import('../api/chat');
      const res = await chatAPI.getMessages(sessionId);
      setMessages(res.data);
      setCurrentSession(sessionId);
    } catch (err) {
      console.error('Failed to load session');
    }
  };

  const handleSend = async () => {
    if (!message.trim()) return;
    setError('');
    setLoading(true);

    const userMessage = message;
    setMessage('');

    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      const { chatAPI } = await import('../api/chat');
      const res = await chatAPI.chat(message, currentSession, selectedKB, useWebSearch);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.response,
        intent: res.data.intent,
        confidence: res.data.confidence,
        sources: res.data.sources
      }]);

      if (!currentSession && res.data.session_id) {
        setCurrentSession(res.data.session_id);
        fetchSessions();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    setCurrentSession(null);
    setMessages([]);
    setSelectedKB(null);
    setUseWebSearch(false);
  };

  return (
    <div className="chat-page">
      <ChatSidebar
        sessions={sessions}
        currentSession={currentSession}
        onSelectSession={loadSession}
        onNewChat={startNewChat}
      />

      <div className="chat-main">
        <ChatOptions
          knowledgeBases={knowledgeBases}
          selectedKB={selectedKB}
          setSelectedKB={setSelectedKB}
          useWebSearch={useWebSearch}
          setUseWebSearch={setUseWebSearch}
        />

        <ChatMessages messages={messages} loading={loading} />

        <ChatInput
          message={message}
          setMessage={setMessage}
          onSend={handleSend}
          loading={loading}
        />

        {error && <div className="error-message">{error}</div>}
      </div>
    </div>
  );
}