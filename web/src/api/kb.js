import { httpClient } from './httpClient';

export const kbAPI = {
  list: () => httpClient.get('/api/kb'),
  get: (id) => httpClient.get(`/api/kb/${id}`),
  create: (name, description) => httpClient.post('/api/kb', { name, description }),
  delete: (id) => httpClient.delete(`/api/kb/${id}`),
  getDocuments: (kbId) => httpClient.get(`/api/kb/${kbId}/documents`),
  uploadDocument: (kbId, formData) => httpClient.post(`/api/kb/${kbId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  deleteDocument: (docId) => httpClient.delete(`/api/documents/${docId}`),
};
