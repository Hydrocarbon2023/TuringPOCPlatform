import axios from 'axios';
import {message} from 'antd';

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
  assignReviewer: (id, data) => api.post(`/projects/${id}/assign`, data),
};

export const incubationApi = {
  get: (projectId) => api.get(`/projects/${projectId}/incubation`),
  createOrUpdate: (projectId, data) => api.post(`/projects/${projectId}/incubation`, data),
};

export const pocApi = {
  getList: (projectId) => api.get(`/projects/${projectId}/poc`),
  create: (projectId, data) => api.post(`/projects/${projectId}/poc`, data),
  getDetail: (pocId) => api.get(`/poc/${pocId}`),
  update: (pocId, data) => api.put(`/poc/${pocId}`, data),
};

export const reviewApi = {
  getMyTasks: () => api.get('/reviews/my-tasks'),
  submitReview: (taskId, data) => api.post(`/reviews/${taskId}`, data),
  getIncubationProjects: () => api.get('/reviewer/incubation-projects'),
};

export const commonApi = {
  getAllUsers: () => api.get('/admin/users'),
};

export const fundApi = {
  allocate: (data) => api.post('/funds', data),
  submitExpenditure: (data) => api.post('/expenditures', data),
  getProjectFunds: (projectId) => api.get(`/projects/${projectId}/funds`),
};

export const achievementApi = {
  create: (data) => api.post('/achievements', data),
  getProjectAchievements: (projectId) => api.get(`/projects/${projectId}/achievements`),
};

export const milestoneApi = {
  getProjectMilestones: (projectId) => api.get(`/projects/${projectId}/milestones`),
  updateMilestone: (milestoneId, data) => api.put(`/milestones/${milestoneId}`, data),
};

export const commentApi = {
  getProjectComments: (projectId) => api.get(`/projects/${projectId}/comments`),
  createComment: (projectId, data) => api.post(`/projects/${projectId}/comments`, data),
};

export const supporterApi = {
  getProjects: () => api.get('/supporter/projects'),
  submitIntention: (data) => api.post('/support/intentions', data),
  getProjectIntentions: (projectId) => api.get(`/projects/${projectId}/intentions`),
  updateIntentionStatus: (projectId, data) => api.put(`/projects/${projectId}/intentions`, data),
  // 资源管理
  createResource: (data) => api.post('/supporter/resources', data),
  getMyResources: () => api.get('/supporter/my-resources'),
  getResourceApplications: (resourceId) => api.get(`/resources/${resourceId}/applications`),
  handleApplication: (applicationId, data) => api.put(`/applications/${applicationId}/handle`, data),
};

export const resourceApi = {
  getPublicResources: (params) => api.get('/public/resources', {params}),
  applyResource: (resourceId, data) => api.post(`/resources/${resourceId}/apply`, data),
  getMyApplications: () => api.get('/my/resource-applications'),
};

export const statisticsApi = {
  getStatistics: () => api.get('/statistics'),
  getUserStatistics: () => api.get('/statistics/user'),
  getReviewerStatistics: () => api.get('/statistics/reviewer'),
  getSupporterStatistics: () => api.get('/statistics/supporter'),
};

export default api;
