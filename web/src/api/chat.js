import apiClient from './client';

export const chatAPI = {
  getSessions: () =>
    apiClient.get('/api/sessions'),

  createSession: (kbId, title) =>
    apiClient.post('/api/sessions', { kb_id: kbId, title }),

  getMessages: (sessionId) =>
    apiClient.get(`/api/sessions/${sessionId}/messages`),

  chat: (message, sessionId, kbIds, enableWebSearch) =>
    apiClient.post('/api/chat', {
      message,
      session_id: sessionId,
      kb_ids: kbIds,
      enable_web_search: enableWebSearch
    }),
};