import apiClient from './client';

export const settingsAPI = {
  get: () =>
    apiClient.get('/settings'),

  update: (key, value) =>
    apiClient.post('/settings', null, { params: { key, value } }),
};