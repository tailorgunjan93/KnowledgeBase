import httpClient from './httpClient';

export const get = () => httpClient.get('/auth/settings');

export const update = (key, value) => httpClient.post('/auth/settings', { key, value });

export const getLLMProvider = () => httpClient.get('/api/llm-provider');

export const fetchModels = (provider, apiKey) =>
  httpClient.get('/api/models', {
    headers: {
      ...(provider ? { 'X-Provider': provider } : {}),
      ...(apiKey   ? { 'X-API-Key': apiKey }    : {}),
    },
  });
