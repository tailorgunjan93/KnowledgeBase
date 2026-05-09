import httpClient from './httpClient';

// Chat sessions
export const chatAPI = {
  getSessions: () => httpClient.get('/api/sessions'),
  createSession: (data) => httpClient.post('/api/sessions', data),
  getMessages: (sessionId) => httpClient.get(`/api/sessions/${sessionId}/messages`),
  sendMessage: (payload) => httpClient.post('/api/chat', payload),
};
