import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

const api = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  users: () => api.get('/auth/users'),
};

export const incidentsAPI = {
  list: (params = {}) => api.get('/incidents', { params }),
  get: (id) => api.get(`/incidents/${id}`),
  create: (data) => api.post('/incidents', data),
  update: (id, data) => api.patch(`/incidents/${id}`, data),
  delete: (id) => api.delete(`/incidents/${id}`),
  classify: (data) => api.post('/classify', data),
};

export const alertsAPI = {
  list: (params = {}) => api.get('/alerts', { params }),
  create: (data) => api.post('/alerts', data),
};

export const assetsAPI = {
  list: () => api.get('/assets'),
  create: (data) => api.post('/assets', data),
};

export const playbooksAPI = {
  list: (params = {}) => api.get('/playbooks/', { params }),
  get: (id) => api.get(`/playbooks/${id}`),
  create: (data) => api.post('/playbooks/', data),
  execute: (playbookId, incidentId) => api.post(`/playbooks/${playbookId}/execute/${incidentId}`),
  updateStep: (executionId, data) => api.patch(`/playbooks/executions/${executionId}/step`, data),
  getExecutions: (incidentId) => api.get(`/playbooks/executions/incident/${incidentId}`),
};

export const dashboardAPI = {
  get: () => api.get('/dashboard/'),
  auditLogs: (limit = 100) => api.get(`/dashboard/audit-logs?limit=${limit}`),
  typeStats: () => api.get('/dashboard/stats/types'),
};

export default api;
