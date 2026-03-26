/**
 * services/api.js — Axios instance + typed API helpers.
 * All API calls go through this module.
 */

import axios from "axios";

// ── Axios instance ────────────────────────────────────────────────────
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  timeout: 120000,  // 120s — first request loads ML models
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token") || 
              localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Global response error handler
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ─────────────────────────────────────────────────────────────
export const authAPI = {
  login:   (email, password) => api.post("/api/auth/login", { email, password }),
  register:(data) => api.post("/api/auth/register", data),
  me:      () => api.get("/api/auth/me"),
  refresh: () => api.post("/api/auth/refresh"),
};

// ── Tickets ───────────────────────────────────────────────────────────
export const ticketsAPI = {
  // 120s timeout: first submit loads embedding + LLM models
  submit: (data) => api.post("/api/tickets/", data, { timeout: 120000 }),
  list:   (params) => api.get("/api/tickets/", { params }),
  get:    (id) => api.get(`/api/tickets/${id}`),
  explain:(id) => api.get(`/api/tickets/${id}/explain`),
  similar:(id) => api.get(`/api/tickets/${id}/similar`),
  updateStatus: (id, data) => api.patch(`/api/tickets/${id}/status`, data),
  byUser: (uid) => api.get(`/api/tickets/user/${uid}`),
};

// ── Feedback ──────────────────────────────────────────────────────────
export const feedbackAPI = {
  approve: (ticketId, data = {}) => api.post(`/api/feedback/${ticketId}/approve`, data),
  edit:    (ticketId, data) => api.post(`/api/feedback/${ticketId}/edit`, data),
  reject:  (ticketId, data) => api.post(`/api/feedback/${ticketId}/reject`, data),
  stats:   () => api.get("/api/feedback/stats"),
};

// ── Agents ────────────────────────────────────────────────────────────
export const agentsAPI = {
  queue:    () => api.get("/api/agents/queue"),
  workload: () => api.get("/api/agents/workload"),
  assign:   (ticketId, agentId) =>
    api.post(`/api/agents/${ticketId}/assign`, null, { params: { agent_id: agentId } }),
};

// ── Analytics ─────────────────────────────────────────────────────────
export const analyticsAPI = {
  overview:             () => api.get("/api/analytics/overview"),
  modelPerformance:     () => api.get("/api/analytics/model-performance"),
  confidenceDist:       (days) => api.get("/api/analytics/confidence-distribution", { params: { days } }),
  ticketVolume:         (days) => api.get("/api/analytics/ticket-volume",           { params: { days } }),
  slaBreakdown:         () => api.get("/api/analytics/sla-breakdown"),
  rootCauseAlerts:      (status) => api.get("/api/analytics/root-cause-alerts",    { params: { status } }),
};

// ── Admin ─────────────────────────────────────────────────────────────
export const adminAPI = {
  modelVersions:    () => api.get("/api/admin/model-versions"),
  triggerRetrain:   () => api.post("/api/admin/retrain"),
  knowledgeBase:    (params) => api.get("/api/admin/knowledge-base", { params }),
  systemHealth:     () => api.get("/api/admin/system-health"),
};

// ── Security ──────────────────────────────────────────────────────────
export const securityAPI = {
  threats:        (params) => api.get("/api/security/threats", { params }),
  stats:          () => api.get("/api/security/stats"),
  playbook:       (type) => api.get(`/api/security/playbook/${type}`),
  acknowledge:    (id) => api.post(`/api/security/${id}/acknowledge`),
  resolve:        (id) => api.post(`/api/security/${id}/resolve`),
  getLogs:        (id) => api.get(`/api/security/${id}/logs`),
  incidentReport: (id, data) => api.post(`/api/security/${id}/incident-report`, data),
  analyzeTicket:  (data) => api.post("/api/security/analyze-ticket", data),
  escalateTicket: (data) => api.post("/api/security/escalate-ticket", data),
};

// ── Queue Monitor ─────────────────────────────────────────────────────
export const queueAPI = {
  status:         () => api.get("/api/queue/status"),
  performance:    (hours = 24) => api.get("/api/queue/performance", { params: { hours } }),
  stageBreakdown: (hours = 24) => api.get("/api/queue/stage-breakdown", { params: { hours } }),
};

// ── Simulation ────────────────────────────────────────────────────────
export const simulationAPI = {
  start:  (config) => api.post("/api/simulation/start", config),
  stop:   () => api.post("/api/simulation/stop"),
  status: () => api.get("/api/simulation/status"),
};

// ── Ticket Images ─────────────────────────────────────────────────────
export const imagesAPI = {
  upload: (ticketId, files) => {
    const formData = new FormData();
    files.forEach((f) => formData.append("images", f));
    return api.post(`/api/tickets/${ticketId}/images`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000,
    });
  },
  getUrl: (ticketId, filename) => `/api/tickets/${ticketId}/images/${filename}`,
};

export default api;
