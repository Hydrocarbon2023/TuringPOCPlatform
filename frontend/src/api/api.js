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
  register: (data) => api.post('/register', data), // 公开注册
  adminCreateUser: (data) => api.post('/admin/users', data), // 管理员创建
};

export const projectApi = {
  create: (data) => api.post('/projects', data),
  getAll: () => api.get('/projects'),
  getDetail: (id) => api.get(`/projects/${id}`),
  audit: (id, data) => api.post(`/projects/${id}/audit`, data),
  assignExpert: (id, data) => api.post(`/projects/${id}/assign`, data), // { expert_id, deadline }
};

export const reviewApi = {
  getMyTasks: () => api.get('/reviews/my-tasks'), // 获取真数据
  submitReview: (taskId, data) => api.post(`/reviews/${taskId}`, data),
};

export const commonApi = {
  getAllUsers: () => api.get('/admin/users'),
};

export default api;
