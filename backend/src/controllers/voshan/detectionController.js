/**
 * Detection Controller
 * Handles suspicious behavior detection requests
 */

const mlService = require('../../services/voshan/mlService');
const websocketService = require('../../services/voshan/websocketService');
const notificationService = require('../../services/voshan/notificationService');
const Alert = require('../../models/voshan/alertModel');

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
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'No video file provided'
      });
    }

    const options = {
      saveOutput: req.body.saveOutput !== 'false'
    };

    // Process video through ML service
    const result = await mlService.processUploadedVideo(req.file, options);

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: 'Error processing video',
        error: result.error,
        details: result.details
      });
    }

    // Save alerts to database
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
          cameraId: req.body.cameraId || null,
          details: alert.details,
          videoInfo: {
            outputVideo: result.data.output_video,
            logJson: result.data.log_json,
            logCsv: result.data.log_csv
          }
        });

        await alertDoc.save();
        savedAlerts.push(alertDoc);

        // Broadcast alert via WebSocket
        websocketService.broadcastAlert({
          alertId: alert.alert_id,
          type: alert.type,
          severity: alert.severity,
          timestamp: alert.timestamp,
          cameraId: req.body.cameraId || null,
          details: alert.details
        });

        // Send notification
        await notificationService.sendHighPriorityAlert({
          alertId: alert.alert_id,
          type: alert.type,
          severity: alert.severity,
          timestamp: alert.timestamp,
          cameraId: req.body.cameraId || null
        });
      } catch (saveError) {
        console.error('Error saving alert:', saveError);
        // Continue saving other alerts even if one fails
      }
    }

    res.json({
      success: true,
      message: 'Video processed successfully',
      data: {
        videoInfo: result.data.video_info,
        totalFrames: result.data.total_frames,
        totalDetections: result.data.total_detections,
        totalAlerts: result.data.total_alerts,
        alerts: savedAlerts,
        outputVideo: result.data.output_video,
        logJson: result.data.log_json,
        logCsv: result.data.log_csv
      }
    });
  } catch (error) {
    console.error('Error in processVideo:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
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
        savedAlerts.push(alertDoc);

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

