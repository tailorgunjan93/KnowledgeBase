import httpClient from './httpClient';

export const ragQuery = (payload) => httpClient.post('/api/chat', payload);
export const submitFeedback = (payload) => httpClient.post('/api/feedback', payload);
