import apiClient from './client';

export const authAPI = {
  signup: (username, email, password) =>
    apiClient.post('/auth/signup', {
      username,
      email: email || null,  // Send null if empty instead of empty string
      password
    }),

  login: (username, password) =>
    apiClient.post('/auth/login', { username, password }),

  getMe: () =>
    apiClient.get('/auth/me'),
};