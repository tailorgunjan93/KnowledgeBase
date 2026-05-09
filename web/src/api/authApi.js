import httpClient from './httpClient';

export const login = (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  return httpClient.post('/auth/login', formData);
};

export const getMe = () => httpClient.get('/auth/me');

export const register = (data) => httpClient.post('/auth/register', data);
