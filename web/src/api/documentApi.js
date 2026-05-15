import httpClient from './httpClient';

export const listKnowledgeBases = () => httpClient.get('/api/kb');
export const getKnowledgeBase = (kbId) => httpClient.get(`/api/kb/${kbId}`);
export const createKnowledgeBase = (name, description) => httpClient.post('/api/kb', { name, description });
export const deleteKnowledgeBase = (kbId) => httpClient.delete(`/api/kb/${kbId}`);

export const getDocuments = (kbId) => httpClient.get(`/api/kb/${kbId}/documents`);
export const uploadDocument = (kbId, formData, onProgress) =>
  httpClient.post(`/api/kb/${kbId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      if (onProgress) onProgress(percentCompleted);
    }
  });

export const deleteDocument = (docId) => httpClient.delete(`/api/documents/${docId}`);
export const searchDocuments = (payload) => httpClient.post('/api/search', payload);

// ── KB Members ────────────────────────────────────────────────────────────────
export const listKBMembers    = (kbId)                      => httpClient.get(`/api/kb/${kbId}/members`);
export const addKBMember      = (kbId, username, role)      => httpClient.post(`/api/kb/${kbId}/members`, { username, role });
export const updateKBMember   = (kbId, userId, role)        => httpClient.put(`/api/kb/${kbId}/members/${userId}`, { role });
export const removeKBMember   = (kbId, userId)              => httpClient.delete(`/api/kb/${kbId}/members/${userId}`);
