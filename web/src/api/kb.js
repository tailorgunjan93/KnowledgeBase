import apiClient from './client';

export const kbAPI = {
  list: (skip = 0, limit = 20) =>
    apiClient.get('/api/kb', { params: { skip, limit } }),

  get: (kbId) =>
    apiClient.get(`/api/kb/${kbId}`),

  create: (name, description) =>
    apiClient.post('/api/kb', { name, description }),

  delete: (kbId) =>
    apiClient.delete(`/api/kb/${kbId}`),

  getDocuments: (kbId, skip = 0, limit = 100) =>
    apiClient.get(`/api/kb/${kbId}/documents`, { params: { skip, limit } }),

  uploadDocument: (kbId, formData) =>
    apiClient.post(`/api/kb/${kbId}/documents`, formData),

  deleteDocument: (docId) =>
    apiClient.delete(`/api/documents/${docId}`),
};