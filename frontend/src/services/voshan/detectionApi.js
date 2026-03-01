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
  // Disable automatic retries to prevent duplicate requests
  validateStatus: function (status) {
    return status >= 200 && status < 500; // Don't throw for 4xx errors
  },
});

// Request deduplication: Track active requests to prevent duplicates
const activeRequests = new Map();

/**
 * Generate a unique key for a request based on file and options
 */
function getRequestKey(videoFile, options) {
  // Use file name, size, and last modified time to create unique key
  const fileKey = `${videoFile.name}_${videoFile.size}_${videoFile.lastModified}`;
  const optionsKey = JSON.stringify({
    cameraId: options.cameraId,
    saveOutput: options.saveOutput
  });
  return `process-video_${fileKey}_${optionsKey}`;
}

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
  // Check if request was already aborted
  if (options.signal?.aborted) {
    throw new Error('Request was aborted');
  }

  // Check for duplicate request - if same file is already being processed, return existing promise
  const requestKey = getRequestKey(videoFile, options);
  if (activeRequests.has(requestKey)) {
    const existingRequest = activeRequests.get(requestKey);
    console.warn(`[detectionApi] Duplicate request detected for ${requestKey}, reusing existing request`);
    
    // If there's a progress callback, we can't reuse the request easily
    // Instead, return the existing promise but log a warning
    if (onUploadProgress) {
      console.warn('[detectionApi] Progress callback provided but request already exists - progress may not update correctly');
    }
    
    return existingRequest;
  }

  const formData = new FormData();
  formData.append('video', videoFile);
  if (options.cameraId) {
    formData.append('cameraId', options.cameraId);
  }
  if (options.saveOutput !== undefined) {
    formData.append('saveOutput', options.saveOutput.toString());
  }
  // Add batch size for optimized processing
  if (options.batchSize) {
    formData.append('batch_size', options.batchSize.toString());
  }

  // Create the request promise
  const requestPromise = (async () => {
    try {
      const response = await detectionApi.post('/process-video', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          // Check if aborted before updating progress
          if (options.signal?.aborted) {
            return;
          }
          if (onUploadProgress && progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onUploadProgress(percentCompleted);
          }
        },
        timeout: 900000, // 15 minutes - matches backend timeout for large video processing
        // Prevent automatic retries
        maxRedirects: 0,
        // Add abort signal to cancel request if needed
        signal: options.signal || undefined,
      });
      
      return response;
    } catch (error) {
      // If aborted, clean up immediately
      if (error.name === 'AbortError' || error.name === 'CanceledError' || options.signal?.aborted) {
        activeRequests.delete(requestKey);
      }
      throw error;
    } finally {
      // Remove from active requests when done (success or error)
      activeRequests.delete(requestKey);
    }
  })();
  
  // Handle abort signal if provided
  if (options.signal) {
    options.signal.addEventListener('abort', () => {
      activeRequests.delete(requestKey);
    });
  }

  // Store the active request
  activeRequests.set(requestKey, requestPromise);

  try {
    const response = await requestPromise;

    // Check if response indicates an error
    if (response.status >= 400) {
      const errorData = response.data || {};
      return {
        success: false,
        message: errorData.message || 'Error processing video',
        error: errorData.error || `Request failed with status code ${response.status}`,
        details: errorData.details || errorData
      };
    }

    return response.data;
  } catch (error) {
    // Remove from active requests on error (already done in finally, but ensure it's removed)
    activeRequests.delete(requestKey);
    
    // Handle axios errors
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data || {};
      return {
        success: false,
        message: errorData.message || 'Error processing video',
        error: errorData.error || error.message || `Request failed with status code ${error.response.status}`,
        details: errorData.details || {
          status: error.response.status,
          statusText: error.response.statusText,
          data: errorData
        }
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        success: false,
        message: 'No response from server',
        error: error.message || 'Network error',
        details: {
          code: error.code,
          message: 'The server did not respond. Please check if the backend is running.'
        }
      };
    } else {
      // Error setting up request
      return {
        success: false,
        message: 'Request setup error',
        error: error.message || 'Unknown error',
        details: {
          code: error.code
        }
      };
    }
  }
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

/**
 * Get full URL for a captured alert frame image (exact frame when alert triggered).
 * Uses full backend URL so images load reliably (avoids proxy path issues).
 * @param {string} filename - Frame image filename (e.g. from alert.frame_image or alert.frameImage)
 * @returns {string|null} Full URL or null if no filename
 */
export const getAlertFrameImageUrl = (filename) => {
  if (!filename || typeof filename !== 'string') return null;
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
  const base = apiUrl.replace(/\/api\/?$/, '') || 'http://localhost:5000';
  // Cache-bust so browser doesn't show old cached (e.g. placeholder) content for this URL
  return `${base}/api/voshan/detection/alert-frames/${encodeURIComponent(filename)}?t=2`;
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

