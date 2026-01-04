/**
 * Detection Controller
 * Handles suspicious behavior detection requests
 */

const mlService = require('../../services/voshan/mlService');
const websocketService = require('../../services/voshan/websocketService');
const notificationService = require('../../services/voshan/notificationService');
const Alert = require('../../models/voshan/alertModel');
const crypto = require('crypto');

// Track active and completed processing requests to prevent duplicates
const activeProcessingRequests = new Map();
const completedProcessingRequests = new Map(); // Track completed requests for a period

/**
 * Health check for ML service
 */
exports.checkMLServiceHealth = async (req, res) => {
  try {
    const health = await mlService.checkHealth();
    res.json(health);
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error checking ML service health',
      error: error.message
    });
  }
};

/**
 * Process uploaded video file
 */
exports.processVideo = async (req, res) => {
  let requestId = null;
  
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'No video file provided'
      });
    }

    // Generate request ID based on file properties to detect duplicates
    // Since multer uses diskStorage, we use filename + size + first/last bytes for hash
    // This prevents processing the same file multiple times even if connection resets
    const fs = require('fs');
    let fileHash = '';
    
    try {
      // Read first 1KB and last 1KB of file to create a content-based hash
      // This is faster than reading the entire file for large videos
      const filePath = req.file.path;
      const fileStats = fs.statSync(filePath);
      const fileSize = fileStats.size;
      
      // Read first 1024 bytes
      const fd = fs.openSync(filePath, 'r');
      const firstChunk = Buffer.alloc(Math.min(1024, fileSize));
      fs.readSync(fd, firstChunk, 0, Math.min(1024, fileSize), 0);
      
      // Read last 1024 bytes if file is large enough
      let lastChunk = Buffer.alloc(0);
      if (fileSize > 1024) {
        lastChunk = Buffer.alloc(Math.min(1024, fileSize - 1024));
        fs.readSync(fd, lastChunk, 0, Math.min(1024, fileSize - 1024), Math.max(0, fileSize - 1024));
      }
      fs.closeSync(fd);
      
      // Create hash from original filename, size, and content chunks
      fileHash = crypto.createHash('md5')
        .update(req.file.originalname || req.file.filename || '')
        .update(String(fileSize))
        .update(firstChunk)
        .update(lastChunk)
        .digest('hex');
    } catch (hashError) {
      // Fallback to filename + size if hash calculation fails
      console.warn(`[processVideo] Error calculating file hash, using fallback:`, hashError.message);
      fileHash = crypto.createHash('md5')
        .update(req.file.originalname || req.file.filename || '')
        .update(String(req.file.size || 0))
        .digest('hex');
    }
    
    requestId = `req-${fileHash}`;
    
    // Clean up stale entries
    const now = Date.now();
    
    // Clean active requests older than 30 minutes
    for (const [id, info] of activeProcessingRequests.entries()) {
      if (now - info.startTime > 30 * 60 * 1000) {
        activeProcessingRequests.delete(id);
        console.log(`[${id}] Removed stale active processing entry`);
      }
    }
    
    // Clean completed requests older than 1 hour
    for (const [id, info] of completedProcessingRequests.entries()) {
      if (now - info.completedTime > 60 * 60 * 1000) {
        completedProcessingRequests.delete(id);
      }
    }
    
    // Check if this exact file was already completed recently (within last hour)
    if (completedProcessingRequests.has(requestId)) {
      const completedInfo = completedProcessingRequests.get(requestId);
      const timeSinceCompletion = Math.round((now - completedInfo.completedTime) / 1000);
      console.warn(`[${requestId}] This video was already processed ${timeSinceCompletion}s ago, returning cached result`);
      
      // Return success response indicating it was already processed
      return res.json({
        success: true,
        message: 'This video was already processed recently. Reusing previous results.',
        alreadyProcessed: true,
        requestId: requestId,
        data: completedInfo.resultData || null
      });
    }
    
    // Check if this request is currently being processed
    if (activeProcessingRequests.has(requestId)) {
      const existingRequest = activeProcessingRequests.get(requestId);
      const timeSinceStart = Math.round((now - existingRequest.startTime) / 1000);
      console.warn(`[${requestId}] Duplicate request detected (started ${timeSinceStart}s ago), ignoring...`);
      return res.status(409).json({
        success: false,
        message: 'This video is already being processed. Please wait for the current processing to complete.',
        requestId: requestId,
        startedAt: existingRequest.startTime
      });
    }

    // Mark request as active
    activeProcessingRequests.set(requestId, {
      startTime: now,
      filename: req.file.filename,
      fileHash: fileHash
    });
    
    console.log(`[${requestId}] Starting video processing...`);

    // Set headers for long-running request (before processing starts)
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('Cache-Control', 'no-cache');

    const options = {
      saveOutput: req.body.saveOutput !== 'false'
    };

    // Process video through ML service
    const result = await mlService.processUploadedVideo(req.file, options);
    console.log(`[${requestId}] ML service response:`, {
      success: result.success,
      hasData: !!result.data,
      dataKeys: result.data ? Object.keys(result.data) : []
    });

    if (!result.success) {
      // Provide more detailed error information
      let errorMessage = 'Error processing video';
      let errorDetails = result.error || 'Unknown error';
      
      // Check for common connection errors
      if (result.error?.includes('ECONNREFUSED') || result.error?.includes('connect') || result.details?.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to ML service';
        errorDetails = 'The Python ML service is not running or not accessible. Please ensure it is running on port 5001.';
      } else if (result.error?.includes('ECONNRESET') || result.error?.includes('CONNECTION_RESET') || result.details?.code === 'ECONNRESET') {
        errorMessage = 'Connection was reset by ML service';
        errorDetails = result.details?.suggestion || 'The ML service connection was reset during processing. This usually happens when using Flask development server for long videos. Please use Gunicorn (production server) instead. Run: cd backend/voshan/ml-service && python run_production.py';
      } else if (result.error?.includes('timeout') || result.details?.code === 'ETIMEDOUT') {
        errorMessage = 'Request timed out';
        errorDetails = 'The ML service took too long to respond. The video may be too large or the service is overloaded.';
      } else if (result.details?.error) {
        errorDetails = result.details.error;
      }
      
      console.error('ML Service Error:', {
        error: result.error,
        details: result.details,
        message: errorMessage
      });
      
      return res.status(500).json({
        success: false,
        message: errorMessage,
        error: errorDetails,
        details: result.details
      });
    }

    // Validate ML service response structure
    if (!result.data) {
      console.error(`[${requestId}] ML service returned success but no data`);
      return res.status(500).json({
        success: false,
        message: 'ML service returned invalid response',
        error: 'No data in ML service response'
      });
    }

    // Save alerts to database
    const alerts = result.data?.alerts || [];
    console.log(`[${requestId}] Processing ${alerts.length} alerts from ML service`);
    const savedAlerts = [];

    for (const alert of alerts) {
      try {
        // Validate alert structure
        if (!alert || !alert.alert_id) {
          console.warn('Skipping invalid alert:', alert);
          continue;
        }

        const alertDoc = new Alert({
          alertId: alert.alert_id || alert.alertId,
          type: alert.type,
          severity: alert.severity,
          timestamp: new Date((alert.timestamp || 0) * 1000),
          frame: alert.frame || null,
          cameraId: req.body.cameraId || null,
          details: alert.details || {},
          videoInfo: {
            outputVideo: result.data?.output_video || null,
            logJson: result.data?.log_json || null,
            logCsv: result.data?.log_csv || null
          }
        });

        await alertDoc.save();
        // Convert Mongoose document to plain object for JSON response
        savedAlerts.push(alertDoc.toObject());

        // Broadcast alert via WebSocket (non-blocking)
        try {
          websocketService.broadcastAlert({
            alertId: alert.alert_id || alert.alertId,
            type: alert.type,
            severity: alert.severity,
            timestamp: alert.timestamp,
            cameraId: req.body.cameraId || null,
            details: alert.details || {}
          });
        } catch (wsError) {
          console.error('Error broadcasting alert via WebSocket:', wsError);
        }

        // Send notification (non-blocking - don't await to avoid delays)
        notificationService.sendHighPriorityAlert({
          alertId: alert.alert_id || alert.alertId,
          type: alert.type,
          severity: alert.severity,
          timestamp: alert.timestamp,
          cameraId: req.body.cameraId || null
        }).catch(notifError => {
          console.error('Error sending notification:', notifError);
        });
      } catch (saveError) {
        console.error('Error saving alert:', saveError);
        // Continue saving other alerts even if one fails
      }
    }

    // Prepare response with safe property access
    const responseData = {
      videoInfo: result.data?.video_info || {},
      totalFrames: result.data?.total_frames || 0,
      totalDetections: result.data?.total_detections || 0,
      totalAlerts: result.data?.total_alerts || alerts.length,
      alerts: savedAlerts,
      outputVideo: result.data?.output_video || null,
      logJson: result.data?.log_json || null,
      logCsv: result.data?.log_csv || null
    };

    console.log(`[${requestId}] Sending success response with:`, {
      totalFrames: responseData.totalFrames,
      totalAlerts: responseData.totalAlerts,
      savedAlertsCount: savedAlerts.length,
      sampleAlert: savedAlerts.length > 0 ? {
        frame: savedAlerts[0].frame,
        type: savedAlerts[0].type,
        hasFrame: savedAlerts[0].frame !== undefined && savedAlerts[0].frame !== null
      } : null
    });

    // Move from active to completed requests
    activeProcessingRequests.delete(requestId);
    completedProcessingRequests.set(requestId, {
      completedTime: Date.now(),
      filename: req.file.filename,
      resultData: responseData
    });

    // Send response with error handling for large responses
    try {
      // Check if response headers were already sent (shouldn't happen, but safety check)
      if (res.headersSent) {
        console.warn(`[${requestId}] Response headers already sent, cannot send response`);
        return;
      }

      // Send response
      res.json({
        success: true,
        message: 'Video processed successfully',
        data: responseData,
        requestId: requestId // Include request ID so frontend can track it
      });
      
      console.log(`[${requestId}] Response sent successfully`);
    } catch (sendError) {
      console.error(`[${requestId}] Error sending response:`, sendError);
      // If headers not sent yet, try to send error response
      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          message: 'Error sending response',
          error: sendError.message,
          requestId: requestId
        });
      }
    }
  } catch (error) {
    console.error(`[${requestId || 'unknown'}] Error in processVideo:`, error);
    console.error('Error stack:', error.stack);
    
    // Remove from active requests on error
    if (requestId) {
      activeProcessingRequests.delete(requestId);
    }
    
    // Provide more detailed error information
    let errorMessage = 'Internal server error';
    let errorDetails = error.message || 'Unknown error';
    
    // Check if it's an ML service connection error
    if (error.code === 'ECONNREFUSED' || error.message?.includes('ECONNREFUSED')) {
      errorMessage = 'Cannot connect to ML service';
      errorDetails = 'The Python ML service is not running or not accessible. Please ensure it is running on port 5001.';
    } else if (error.code === 'ECONNRESET' || error.message?.includes('ECONNRESET') || error.message?.includes('CONNECTION_RESET')) {
      errorMessage = 'Connection was reset by ML service';
      errorDetails = 'The ML service connection was reset. This usually happens when using Flask development server for long videos. Please use Gunicorn (production server) instead. Run: cd backend/voshan/ml-service && python run_production.py';
    } else if (result?.error?.includes('ECONNRESET') || result?.details?.code === 'ECONNRESET') {
      // Error from ML service client (mlService.processUploadedVideo)
      errorMessage = 'Connection was reset by ML service';
      errorDetails = result.details?.suggestion || 'The ML service connection was reset during processing. Please use Gunicorn (production server) instead of Flask dev server. Run: cd backend/voshan/ml-service && python run_production.py';
    } else if (error.response) {
      // Error from ML service
      errorMessage = error.response.data?.message || errorMessage;
      errorDetails = error.response.data?.error || errorDetails;
    }
    
    res.status(500).json({
      success: false,
      message: errorMessage,
      error: errorDetails,
      details: process.env.NODE_ENV === 'development' ? {
        stack: error.stack,
        code: error.code
      } : undefined
    });
  }
};

/**
 * Process single frame (for real-time streaming)
 */
exports.processFrame = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'No frame image provided'
      });
    }

    const cameraId = req.body.cameraId || req.query.cameraId || null;
    const frameBuffer = req.file.buffer;

    // Process frame through ML service
    const result = await mlService.processFrame(frameBuffer, cameraId);

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: 'Error processing frame',
        error: result.error,
        details: result.details
      });
    }

    // Save alerts to database if any
    const alerts = result.data.alerts || [];
    const savedAlerts = [];

    for (const alert of alerts) {
      try {
        const alertDoc = new Alert({
          alertId: alert.alert_id,
          type: alert.type,
          severity: alert.severity,
          timestamp: new Date(alert.timestamp * 1000),
          frame: alert.frame,
          cameraId: cameraId,
          details: alert.details
        });

        await alertDoc.save();
        // Convert Mongoose document to plain object for JSON response
        savedAlerts.push(alertDoc.toObject());

        // Broadcast alert via WebSocket
        websocketService.broadcastAlert({
          alertId: alert.alert_id,
          type: alert.type,
          severity: alert.severity,
          timestamp: alert.timestamp,
          cameraId: cameraId,
          details: alert.details
        });

        // Send notification
        await notificationService.sendHighPriorityAlert({
          alertId: alert.alert_id,
          type: alert.type,
          severity: alert.severity,
          timestamp: alert.timestamp,
          cameraId: cameraId
        });
      } catch (saveError) {
        console.error('Error saving alert:', saveError);
      }
    }

    res.json({
      success: true,
      data: {
        detections: result.data.detections,
        alerts: savedAlerts,
        cameraId: cameraId
      }
    });
  } catch (error) {
    console.error('Error in processFrame:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    });
  }
};

/**
 * Get all alerts
 */
exports.getAlerts = async (req, res) => {
  try {
    const {
      page = 1,
      limit = 50,
      type,
      severity,
      cameraId,
      startDate,
      endDate
    } = req.query;

    const query = {};

    if (type) query.type = type;
    if (severity) query.severity = severity;
    if (cameraId) query.cameraId = cameraId;

    if (startDate || endDate) {
      query.timestamp = {};
      if (startDate) query.timestamp.$gte = new Date(startDate);
      if (endDate) query.timestamp.$lte = new Date(endDate);
    }

    const skip = (parseInt(page) - 1) * parseInt(limit);

    const alerts = await Alert.find(query)
      .sort({ timestamp: -1 })
      .skip(skip)
      .limit(parseInt(limit));

    const total = await Alert.countDocuments(query);

    res.json({
      success: true,
      data: {
        alerts,
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total,
          pages: Math.ceil(total / parseInt(limit))
        }
      }
    });
  } catch (error) {
    console.error('Error in getAlerts:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching alerts',
      error: error.message
    });
  }
};

/**
 * Get alert by ID
 */
exports.getAlertById = async (req, res) => {
  try {
    const { id } = req.params;

    const alert = await Alert.findById(id);

    if (!alert) {
      return res.status(404).json({
        success: false,
        message: 'Alert not found'
      });
    }

    res.json({
      success: true,
      data: alert
    });
  } catch (error) {
    console.error('Error in getAlertById:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching alert',
      error: error.message
    });
  }
};

/**
 * Get alerts by camera ID
 */
exports.getAlertsByCamera = async (req, res) => {
  try {
    const { cameraId } = req.params;
    const {
      page = 1,
      limit = 50,
      type,
      severity
    } = req.query;

    const query = { cameraId };

    if (type) query.type = type;
    if (severity) query.severity = severity;

    const skip = (parseInt(page) - 1) * parseInt(limit);

    const alerts = await Alert.find(query)
      .sort({ timestamp: -1 })
      .skip(skip)
      .limit(parseInt(limit));

    const total = await Alert.countDocuments(query);

    res.json({
      success: true,
      data: {
        alerts,
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total,
          pages: Math.ceil(total / parseInt(limit))
        }
      }
    });
  } catch (error) {
    console.error('Error in getAlertsByCamera:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching alerts',
      error: error.message
    });
  }
};

/**
 * Delete alert by ID
 */
exports.deleteAlert = async (req, res) => {
  try {
    const { id } = req.params;

    const alert = await Alert.findByIdAndDelete(id);

    if (!alert) {
      return res.status(404).json({
        success: false,
        message: 'Alert not found'
      });
    }

    res.json({
      success: true,
      message: 'Alert deleted successfully'
    });
  } catch (error) {
    console.error('Error in deleteAlert:', error);
    res.status(500).json({
      success: false,
      message: 'Error deleting alert',
      error: error.message
    });
  }
};

