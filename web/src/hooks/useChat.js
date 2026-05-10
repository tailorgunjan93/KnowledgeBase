import { useState, useCallback } from 'react';
import { chatAPI } from '../api';

export function useChat() {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchSessions = useCallback(async () => {
    try {
      const res = await chatAPI.getSessions();
      setSessions(res.data);
    } catch (err) {
      console.error('Failed to fetch sessions');
    }
  }, []);

  const loadSession = useCallback(async (sessionId) => {
    try {
      const res = await chatAPI.getMessages(sessionId);
      setMessages(res.data);
      setCurrentSession(sessionId);
    } catch (err) {
      console.error('Failed to load session');
    }
  }, []);

  const sendMessage = useCallback(async (message, kbId, enableWebSearch) => {
    if (!message.trim()) return;
    setError('');
    setLoading(true);

    const userMessage = message;
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      // Build payload - send as single kb_id for compatibility
      const payload = {
        message,
        session_id: currentSession,
        kb_ids: kbId ? [kbId] : undefined,
        enable_web_search: enableWebSearch,
      };

      const res = await chatAPI.sendMessage(payload);

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
  }, [currentSession, fetchSessions]);

  const startNewChat = useCallback(() => {
    setCurrentSession(null);
    setMessages([]);
  }, []);

  return {
    sessions,
    currentSession,
    messages,
    loading,
    error,
    fetchSessions,
    loadSession,
    sendMessage,
    startNewChat,
  };
}