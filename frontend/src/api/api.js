import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
    return Promise.reject(error);
  },
);

export const loginUser = (payload) => api.post("/auth/login", payload);
export const registerUser = (payload) => api.post("/auth/register", payload);
export const getMe = () => api.get("/auth/me");
export const updateProfile = (payload) => api.put("/auth/profile", payload);
export const changePassword = (payload) => api.put("/auth/change-password", payload);
export const getNotifications = () => api.get("/auth/notifications");
export const markNotificationRead = (id) => api.put(`/auth/notifications/${id}/read`);
export const markAllNotificationsRead = () => api.put("/auth/notifications/read-all");

export const predictTumor = (formData) => api.post("/predict", formData, {
  headers: { "Content-Type": "multipart/form-data" },
});
export const getHistory = (params = {}) => api.get("/history", { params });
export const getPatientDashboard = () => api.get("/patient/dashboard");
export const getPrediction = (reportId) => api.get(`/prediction/${reportId}`);

export const getDoctorDashboard = () => api.get("/doctor/dashboard");
export const getDoctorReports = (params = {}) => api.get("/doctor/reports", { params });
export const getDoctorPatients = (params = {}) => api.get("/doctor/patients", { params });
export const reviewDoctorReport = (reportId, payload) => api.put(`/doctor/reports/${reportId}/review`, payload);
export const comparePatientReports = (patientId) => api.get(`/doctor/patients/${patientId}/compare`);

export const getAdminDashboard = () => api.get("/admin/dashboard");
export const getAdminUsers = (params = {}) => api.get("/admin/users", { params });
export const createDoctor = (payload) => api.post("/admin/doctors", payload);
export const updateAdminUser = (id, payload) => api.put(`/admin/users/${id}`, payload);
export const setUserActive = (id, isActive) => api.put(`/admin/users/${id}/active`, { is_active: isActive });
export const deleteDoctor = (id) => api.delete(`/admin/doctors/${id}`);
export const getAdminPredictions = (params = {}) => api.get("/admin/predictions", { params });
export const assignDoctor = (reportId, doctorId) => api.put(`/admin/predictions/${reportId}/assign`, { doctor_id: Number(doctorId) });
export const getAuditLogs = () => api.get("/admin/audit-logs");
export const getSystemSettings = () => api.get("/admin/settings");
export const updateSystemSettings = (payload) => api.put("/admin/settings", payload);
export const restoreDatabase = (formData) => api.post("/admin/restore", formData, { headers: { "Content-Type": "multipart/form-data" } });

export async function fetchProtectedBlob(path) {
  const response = await api.get(path, { responseType: "blob" });
  return URL.createObjectURL(response.data);
}

export async function downloadProtected(path, filename) {
  const url = await fetchProtectedBlob(path);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default api;
