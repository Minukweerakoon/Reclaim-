/**
 * Detection Routes
 * API routes for suspicious behavior detection
 */

const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const detectionController = require('../../controllers/voshan/detectionController');
const websocketController = require('../../controllers/voshan/websocketController');
const errorHandler = require('../../middleware/voshan/errorHandler');

// Configure multer for video uploads
const videoStorage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadPath = path.join(__dirname, '../../../uploads/voshan');
    if (!fs.existsSync(uploadPath)) {
      fs.mkdirSync(uploadPath, { recursive: true });
    }
    cb(null, uploadPath);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, 'video-' + uniqueSuffix + path.extname(file.originalname));
  }
});

// Configure multer for frame uploads (in memory)
const frameStorage = multer.memoryStorage();

const videoUpload = multer({
  storage: videoStorage,
  limits: {
    fileSize: 500 * 1024 * 1024 // 500MB limit
  },
  fileFilter: function (req, file, cb) {
    const allowedMimes = [
      'video/mp4',
      'video/avi',
      'video/mov',
      'video/quicktime',
      'video/x-msvideo',
      'video/msvideo'
    ];
    const allowedExt = ['.avi', '.mp4', '.mov', '.mkv', '.webm'];
    const ext = path.extname(file.originalname || '').toLowerCase();
    const mimeOk = allowedMimes.includes(file.mimetype);
    const extOk = allowedExt.includes(ext);
    // Allow if mimetype is in list, or if extension is video and mimetype is generic/empty (e.g. curl sends application/octet-stream)
    if (mimeOk || (extOk && (!file.mimetype || file.mimetype === 'application/octet-stream'))) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only video files are allowed.'));
    }
  }
});

const frameUpload = multer({
  storage: frameStorage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit for images
  },
  fileFilter: function (req, file, cb) {
    const allowedMimes = [
      'image/jpeg',
      'image/jpg',
      'image/png'
    ];
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only image files are allowed.'));
    }
  }
});

// Health check
router.get('/health', detectionController.checkMLServiceHealth);

// WebSocket status
router.get('/websocket/status', websocketController.getWebSocketStatus);

// Process video file
router.post('/process-video', videoUpload.single('video'), detectionController.processVideo);

// Process single frame (for real-time streaming)
router.post('/process-frame', frameUpload.single('frame'), detectionController.processFrame);

// Get all alerts
router.get('/alerts', detectionController.getAlerts);

// Get alert by ID
router.get('/alerts/:id', detectionController.getAlertById);

// Get alerts by camera ID
router.get('/alerts/camera/:cameraId', detectionController.getAlertsByCamera);

// Delete alert
router.delete('/alerts/:id', detectionController.deleteAlert);

// Error handling middleware
router.use(errorHandler);

module.exports = router;

