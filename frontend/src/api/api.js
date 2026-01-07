import axios from 'axios';
import { message } from 'antd';

const api = axios.create({
  baseURL: '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.message || '请求失败';
    message.error(msg);
    return Promise.reject(error);
  }
);

export const userApi = {
  login: (data) => api.post('/login', data),
  register: (data) => api.post('/register', data),
  adminCreateUser: (data) => api.post('/admin/users', data),
};

export const teamApi = {
  create: (data) => api.post('/teams', data),
  getAll: () => api.get('/teams'),
  getMyTeams: () => api.get('/teams/my'),
  inviteMember: (teamId, data) => api.post(`/teams/${teamId}/members`, data),
  getMembers: (teamId) => api.get(`/teams/${teamId}/members`),
};

export const projectApi = {
  create: (data) => api.post('/projects', data),
  getAll: () => api.get('/projects'),
  getDetail: (id) => api.get(`/projects/${id}`),
  audit: (id, data) => api.post(`/projects/${id}/audit`, data),
  assignExpert: (id, data) => api.post(`/projects/${id}/assign`, data),
};

export const reviewApi = {
  getMyTasks: () => api.get('/reviews/my-tasks'),
  submitReview: (taskId, data) => api.post(`/reviews/${taskId}`, data),
};

export const commonApi = {
  getAllUsers: () => api.get('/admin/users'),
};

export default api;
