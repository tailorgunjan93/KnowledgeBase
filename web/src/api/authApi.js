import httpClient from './httpClient';

export const login = (username, password) => {
  return httpClient.post('/auth/login', { username, password });
};

export const getMe = () => httpClient.get('/auth/me');

export const register = (data) => {
  // data should be { username, email?, password }
  return httpClient.post('/auth/register', data);
};
