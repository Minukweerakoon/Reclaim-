/**
 * ML Service Client
 * Communicates with Python ML service for suspicious behavior detection
 */

const axios = require('axios');

class MLService {
  constructor() {
    this.baseURL = process.env.ML_SERVICE_URL || 'http://localhost:5001';
    this.timeout = 300000; // 5 minutes for video processing
  }

  /**
   * Check if ML service is healthy
   */
  async checkHealth() {
    try {
      const response = await axios.get(`${this.baseURL}/api/v1/detect/status`, {
        timeout: 5000
      });
      return {
        healthy: response.data.status === 'healthy',
        modelLoaded: response.data.model_loaded || false,
        gpuAvailable: response.data.gpu_available || false,
        modelInfo: response.data.model_info || {}
      };
    } catch (error) {
      return {
        healthy: false,
        error: error.message
      };
    }
  }

  /**
   * Process a video file
   * @param {string} videoPath - Path to video file
   * @param {Object} options - Processing options
   * @returns {Promise<Object>} Detection results
   */
  async processVideo(videoPath, options = {}) {
    try {
      const FormData = require('form-data');
      const fs = require('fs');
      
      const formData = new FormData();
      formData.append('video_file', fs.createReadStream(videoPath));
      formData.append('save_output', options.saveOutput !== false ? 'true' : 'false');

      const response = await axios.post(
        `${this.baseURL}/api/v1/detect/process-video`,
        formData,
        {
          headers: formData.getHeaders(),
          timeout: this.timeout,
          maxContentLength: Infinity,
          maxBodyLength: Infinity
        }
      );

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        details: error.response?.data || {}
      };
    }
  }

  /**
   * Process a single frame (for real-time streaming)
   * @param {Buffer} frameBuffer - Image buffer
   * @param {string} cameraId - Camera identifier
   * @returns {Promise<Object>} Detection results
   */
  async processFrame(frameBuffer, cameraId = null) {
    try {
      const FormData = require('form-data');
      
      const formData = new FormData();
      formData.append('frame', frameBuffer, {
        filename: 'frame.jpg',
        contentType: 'image/jpeg'
      });
      if (cameraId) {
        formData.append('camera_id', cameraId);
      }

      const response = await axios.post(
        `${this.baseURL}/api/v1/detect/process-frame`,
        formData,
        {
          headers: formData.getHeaders(),
          timeout: 30000 // 30 seconds for frame processing
        }
      );

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        details: error.response?.data || {}
      };
    }
  }

  /**
   * Upload video file and process it
   * @param {Object} file - Multer file object
   * @param {Object} options - Processing options
   * @returns {Promise<Object>} Detection results
   */
  async processUploadedVideo(file, options = {}) {
    try {
      const FormData = require('form-data');
      const fs = require('fs');
      
      const formData = new FormData();
      formData.append('video_file', fs.createReadStream(file.path));
      formData.append('save_output', options.saveOutput !== false ? 'true' : 'false');

      const response = await axios.post(
        `${this.baseURL}/api/v1/detect/process-video`,
        formData,
        {
          headers: formData.getHeaders(),
          timeout: this.timeout,
          maxContentLength: Infinity,
          maxBodyLength: Infinity
        }
      );

      // Clean up uploaded file
      try {
        fs.unlinkSync(file.path);
      } catch (unlinkError) {
        console.error('Error deleting temp file:', unlinkError);
      }

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      // Clean up uploaded file on error
      try {
        const fs = require('fs');
        fs.unlinkSync(file.path);
      } catch (unlinkError) {
        console.error('Error deleting temp file:', unlinkError);
      }

      return {
        success: false,
        error: error.message,
        details: error.response?.data || {}
      };
    }
  }
}

module.exports = new MLService();

