import httpClient from './httpClient';

export const listUsers       = (skip = 0, limit = 50) => httpClient.get('/api/admin/users', { params: { skip, limit } });
export const updateUserRole  = (userId, role)          => httpClient.put(`/api/admin/users/${userId}/role`, { role });
export const getAdminStats   = ()                      => httpClient.get('/api/admin/stats');
