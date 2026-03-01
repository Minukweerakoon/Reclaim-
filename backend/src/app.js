const express = require('express');
const cors = require('cors');
const path = require('path');
const dotenv = require('dotenv');
const compression = require('compression');

// Load environment variables
dotenv.config();

const app = express();

// Middleware
app.use(cors());

// Enable response compression to reduce response size (helps with large JSON responses)
// Exclude Socket.IO paths to avoid interfering with WebSocket connections
app.use(compression({
  filter: (req, res) => {
    // Don't compress Socket.IO requests (WebSocket connections)
    if (req.path && req.path.startsWith('/api/voshan/socket.io')) {
      return false;
    }
    // Compress all responses except if explicitly disabled
    if (req.headers['x-no-compression']) {
      return false;
    }
    // Use compression for all other responses
    return compression.filter(req, res);
  },
  level: 6 // Compression level (0-9, 6 is a good balance)
}));

// Increase body size limits for large video uploads
app.use(express.json({ limit: '500mb' }));
app.use(express.urlencoded({ extended: true, limit: '500mb' }));

// Add keep-alive headers for long-running requests
app.use((req, res, next) => {
  res.setHeader('Connection', 'keep-alive');
  next();
});

// Routes
// TODO: Add your routes here
// app.use('/api/auth', require('./routes/auth'));
// app.use('/api/items', require('./routes/items'));

// Voshan: Serve captured alert frames (exact frame when alert triggered)
// __dirname is backend/src → one level up is backend, then voshan/ml-service/outputs/alert_frames
const alertFramesDir = path.resolve(__dirname, '../voshan/ml-service/outputs/alert_frames');
app.use('/api/voshan/detection/alert-frames', (req, res, next) => {
  res.setHeader('Cache-Control', 'no-cache, must-revalidate');
  next();
}, express.static(alertFramesDir));

// Voshan: Suspicious Behavior Detection Routes
app.use('/api/voshan/detection', require('./routes/voshan/detectionRoutes'));

// Health check route
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Server is running' });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  console.error('Error stack:', err.stack);
  
  // Don't send response if headers already sent
  if (res.headersSent) {
    return next(err);
  }
  
  res.status(err.status || 500).json({ 
    success: false,
    message: 'Something went wrong!', 
    error: process.env.NODE_ENV === 'development' ? err.message : 'Internal server error',
    details: process.env.NODE_ENV === 'development' ? {
      stack: err.stack,
      name: err.name
    } : undefined
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ message: 'Route not found' });
});

module.exports = app;

