/**
 * Detection API Service
 * Handles API calls for suspicious behavior detection
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const detectionApi = axios.create({
  baseURL: `${API_URL}/voshan/detection`,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Check ML service health
 */
export const checkMLServiceHealth = async () => {
  const response = await detectionApi.get('/health');
  return response.data;
};

/**
 * Process video file
 * @param {File} videoFile - Video file to process
 * @param {Object} options - Processing options
 * @param {Function} onUploadProgress - Upload progress callback
 */
export const processVideo = async (videoFile, options = {}, onUploadProgress) => {
  const formData = new FormData();
  formData.append('video', videoFile);
  if (options.cameraId) {
    formData.append('cameraId', options.cameraId);
  }
  if (options.saveOutput !== undefined) {
    formData.append('saveOutput', options.saveOutput.toString());
  }

  const response = await detectionApi.post('/process-video', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onUploadProgress(percentCompleted);
      }
    },
    timeout: 300000, // 5 minutes
  });

  return response.data;
};

/**
 * Process single frame
 * @param {File} frameFile - Image file to process
 * @param {string} cameraId - Camera identifier
 */
export const processFrame = async (frameFile, cameraId = null) => {
  const formData = new FormData();
  formData.append('frame', frameFile);
  if (cameraId) {
    formData.append('cameraId', cameraId);
  }

  const response = await detectionApi.post('/process-frame', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 30000, // 30 seconds
  });

  return response.data;
};

/**
 * Get all alerts with filtering
 * @param {Object} filters - Filter options
 */
export const getAlerts = async (filters = {}) => {
  const params = new URLSearchParams();
  
  if (filters.page) params.append('page', filters.page);
  if (filters.limit) params.append('limit', filters.limit);
  if (filters.type) params.append('type', filters.type);
  if (filters.severity) params.append('severity', filters.severity);
  if (filters.cameraId) params.append('cameraId', filters.cameraId);
  if (filters.startDate) params.append('startDate', filters.startDate);
  if (filters.endDate) params.append('endDate', filters.endDate);

  const response = await detectionApi.get(`/alerts?${params.toString()}`);
  return response.data;
};

/**
 * Get alert by ID
 * @param {string} id - Alert ID
 */
export const getAlertById = async (id) => {
  const response = await detectionApi.get(`/alerts/${id}`);
  return response.data;
};

/**
 * Get alerts by camera ID
 * @param {string} cameraId - Camera identifier
 * @param {Object} filters - Additional filters
 */
export const getAlertsByCamera = async (cameraId, filters = {}) => {
  const params = new URLSearchParams();
  
  if (filters.page) params.append('page', filters.page);
  if (filters.limit) params.append('limit', filters.limit);
  if (filters.type) params.append('type', filters.type);
  if (filters.severity) params.append('severity', filters.severity);

  const response = await detectionApi.get(
    `/alerts/camera/${cameraId}?${params.toString()}`
  );
  return response.data;
};

/**
 * Delete alert
 * @param {string} id - Alert ID
 */
export const deleteAlert = async (id) => {
  const response = await detectionApi.delete(`/alerts/${id}`);
  return response.data;
};

/**
 * Get WebSocket status
 */
export const getWebSocketStatus = async () => {
  const response = await detectionApi.get('/websocket/status');
  return response.data;
};

export default {
  checkMLServiceHealth,
  processVideo,
  processFrame,
  getAlerts,
  getAlertById,
  getAlertsByCamera,
  deleteAlert,
  getWebSocketStatus,
};

