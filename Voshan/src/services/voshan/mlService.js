/**
 * ML Service Client
 * Communicates with Python ML service for suspicious behavior detection
 */

const axios = require('axios');

class MLService {
  constructor() {
    this.baseURL = process.env.ML_SERVICE_URL || 'http://localhost:5001';
    // Increased timeout for large videos - 15 minutes (900000ms)
    // For very large videos, consider processing in chunks
    this.timeout = parseInt(process.env.ML_SERVICE_TIMEOUT) || 900000; // 15 minutes default
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
      // Add batch size for optimized processing (process multiple frames at once)
      formData.append('batch_size', (options.batchSize || 8).toString());

      const response = await axios.post(
        `${this.baseURL}/api/v1/detect/process-video`,
        formData,
        {
          headers: formData.getHeaders(),
          timeout: this.timeout,
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
          validateStatus: function (status) {
            // Don't throw for any status, handle errors manually
            return status >= 200 && status < 600;
          }
        }
      );

      // Check if response indicates an error
      if (response.status >= 400) {
        // Clean up uploaded file
        try {
          fs.unlinkSync(file.path);
        } catch (unlinkError) {
          console.error('Error deleting temp file:', unlinkError);
        }

        // Parse error response (could be JSON or HTML)
        let errorData = response.data;
        let errorMessage = 'ML service returned an error';
        
        // If response is HTML (Flask error page), try to extract useful info
        if (typeof errorData === 'string' && errorData.includes('<!doctype html>')) {
          errorMessage = `ML service error (status ${response.status})`;
          // Try to extract error message from HTML if possible
          const errorMatch = errorData.match(/<h1>(.*?)<\/h1>/);
          if (errorMatch) {
            errorMessage = errorMatch[1];
          }
          errorData = {
            status: response.status,
            message: errorMessage,
            html_response: true
          };
        } else if (typeof errorData === 'object' && errorData !== null) {
          // JSON response
          errorMessage = errorData.message || errorData.error || errorMessage;
        }

        console.error('ML Service Error Response:', {
          status: response.status,
          statusText: response.statusText,
          data: errorData
        });

        return {
          success: false,
          error: errorMessage,
          details: {
            status: response.status,
            statusText: response.statusText,
            data: errorData
          }
        };
      }

      // Clean up uploaded file
      try {
        fs.unlinkSync(file.path);
      } catch (unlinkError) {
        console.error('Error deleting temp file:', unlinkError);
      }

      // Log response structure for debugging
      console.log('ML Service Response Status:', response.status);
      console.log('ML Service Response Keys:', Object.keys(response.data || {}));
      
      // Check if response data indicates an error
      if (response.data && response.data.status === 'error') {
        return {
          success: false,
          error: response.data.message || 'ML service returned error status',
          details: response.data
        };
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

      // Enhanced error logging
      console.error('ML Service Request Error:', {
        code: error.code,
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: `${this.baseURL}/api/v1/detect/process-video`
      });

      // Provide more detailed error information
      let errorMessage = error.message || 'Unknown error';
      let errorDetails = {};

      // Handle connection errors
      if (error.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to ML service. The Python ML service is not running on port 5001.';
        errorDetails = {
          code: 'ECONNREFUSED',
          service_url: this.baseURL,
          suggestion: 'Please start the Python ML service by running: cd Voshan/ml-service && python app.py'
        };
      } else if (error.code === 'ECONNRESET' || error.message?.includes('ECONNRESET') || error.message?.includes('CONNECTION_RESET')) {
        errorMessage = 'Connection was reset by the ML service. This usually means the response was too large or the service encountered an error during processing.';
        errorDetails = {
          code: 'ECONNRESET',
          service_url: this.baseURL,
          suggestion: 'The video may have generated too many alerts. The system now limits alerts in responses. Try processing again, or check the log files for complete results. If the issue persists, try using a production server (gunicorn) instead of Flask dev server.'
        };
      } else if (error.code === 'ETIMEDOUT' || error.message?.includes('timeout')) {
        errorMessage = 'Request timed out. The ML service took too long to respond.';
        errorDetails = {
          code: 'ETIMEDOUT',
          timeout: this.timeout,
          suggestion: 'Try with a smaller video file or check if the ML service is processing correctly'
        };
      } else if (error.response) {
        // Server responded with error
        const responseData = error.response.data;
        
        // Handle HTML error responses (Flask default error pages)
        if (typeof responseData === 'string' && responseData.includes('<!doctype html>')) {
          errorMessage = `ML service error (status ${error.response.status})`;
          // Try to extract error message from HTML
          const titleMatch = responseData.match(/<title>(.*?)<\/title>/i);
          const h1Match = responseData.match(/<h1>(.*?)<\/h1>/i);
          
          if (titleMatch) {
            errorMessage = titleMatch[1];
          } else if (h1Match) {
            errorMessage = h1Match[1];
          }
          
          errorDetails = {
            status: error.response.status,
            statusText: error.response.statusText,
            html_response: true,
            message: errorMessage
          };
        } else if (typeof responseData === 'object' && responseData !== null) {
          // JSON error response
          errorMessage = responseData.error || responseData.message || errorMessage;
          errorDetails = responseData;
        } else {
          errorMessage = error.message || errorMessage;
          errorDetails = {
            status: error.response.status,
            statusText: error.response.statusText,
            data: responseData
          };
        }
      } else if (error.request) {
        // Request was made but no response received
        errorMessage = 'No response from ML service. The service may be down or not responding.';
        errorDetails = {
          code: 'NO_RESPONSE',
          service_url: this.baseURL
        };
      }

      return {
        success: false,
        error: errorMessage,
        details: errorDetails,
        originalError: {
          code: error.code,
          message: error.message
        }
      };
    }
  }
}

module.exports = new MLService();

