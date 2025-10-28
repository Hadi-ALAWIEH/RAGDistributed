import axios from "axios";

const API_BASE = "/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const ragAPI = {
  // Health check
  getHealth: () => api.get("/health"),

  // Search
  search: (query, k = 5) => api.get("/search", { params: { q: query, k } }),

  // RAG query
  ragQuery: (query, k = 5) => api.post("/rag", { q: query, k }),

  // Get documents
  getRawDocuments: (limit = 10) => api.get("/raw", { params: { limit } }),

  getCleanDocuments: (limit = 10) => api.get("/clean", { params: { limit } }),

  // Reload index
  reloadIndex: () => api.post("/reload-index"),
};

export default api;
