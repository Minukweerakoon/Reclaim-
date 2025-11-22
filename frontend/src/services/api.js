import axios from 'axios';

// Detect if we're on mobile and use the correct IP
const getAPIBaseURL = () => {
  // For mobile devices, use the laptop's IP address
  if (/mobile|android|iphone|ipad/i.test(navigator.userAgent)) {
    return 'http://192.168.1.125:5000/api';
  }
  return 'http://localhost:5000/api';
};

const API_BASE_URL = getAPIBaseURL();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.headers['Content-Type'] = 'application/json';
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/login', { email, password }),
  register: (userData) => api.post('/register', userData),
  getProfile: () => api.get('/profile'),
  debugUsers: () => api.get('/debug-users'),
};

export const devicesAPI = {
  registerDevice: (deviceData) => api.post('/devices', deviceData),
  getUserDevices: () => api.get('/devices'),
  getDevice: (deviceId) => api.get(`/devices/${deviceId}`),
  updateDeviceStatus: (deviceId, status, location) => 
    api.post(`/devices/${deviceId}/status`, { status, location }),
  checkAnomaly: (deviceId, behavior, location) =>
    api.post(`/devices/${deviceId}/check-anomaly`, { behavior, location }),
  autoDetectDevice: () => api.get('/devices/auto-detect'),
  updateDeviceLocation: (deviceId) => api.post(`/devices/${deviceId}/update-location`),
  debugMacAddress: () => api.get('/devices/mac-debug'),
  checkNewDevice: () => api.get('/devices/check-new-device'),
  autoRegisterDevice: (deviceData) => api.post('/devices/auto-register', deviceData),
  autoRegisterMobile: () => api.post('/devices/auto-register-mobile'),
};

export const alertsAPI = {
  getAlerts: () => api.get('/alerts'),
  resolveAlert: (alertId) => api.post(`/alerts/${alertId}/resolve`),
  blacklistDevice: (deviceId) => api.post('/blacklist', { device_id: deviceId }),
};

export const systemAPI = {
  health: () => api.get('/health'),
  debugDB: () => api.get('/debug-db'),
};

export default api;