import axios from "axios";

// Base URL API backend
// Di production (same container): /api (relative, Nginx proxy)
// Di development: http://localhost:8001/api (direct ke Docker backend)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor: otomatis tambahkan Bearer token ke setiap request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor: handle 401 (token expired/invalid) → redirect ke login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_info");
      // Hanya redirect jika sedang di halaman admin
      if (window.location.pathname.startsWith("/admin")) {
        window.location.href = "/admin/login";
      }
    }
    return Promise.reject(error);
  }
);

// ==========================================
// AUTH API
// ==========================================
export const authApi = {
  loginWithFirebase: (idToken) =>
    api.post("/auth/firebase/login", { id_token: idToken }),
};

// ==========================================
// USER API
// ==========================================
export const userApi = {
  getMe: () => api.get("/users/me"),
  updateRole: (userId, role) =>
    api.patch(`/users/${userId}/role`, { role }),
};

// ==========================================
// ADMIN API
// ==========================================
export const adminApi = {
  getStats: () => api.get("/admin/stats"),
  getAllUsers: () => api.get("/admin/users"),
};

// ==========================================
// DEVICE API
// ==========================================
export const deviceApi = {
  register: (macAddress) =>
    api.post("/devices/register", { mac_address: macAddress }),
  getUnclaimed: () => api.get("/devices/unclaimed"),
};

export default api;
