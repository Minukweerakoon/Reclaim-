require('dotenv').config();

const express = require('express');
const cors = require('cors');
const compression = require('compression');
const connectDB = require('./config/db');
const { initSupabase } = require('./config/supabase');
const env = require('./config/env');
const { startScheduler } = require('./services/reminderScheduler');
const pythonMLService = require('./services/pythonMLService');
const path = require('path');
const http = require('http');
const wsService = require('./services/wsService');
const voshanWebsocketService = require('./services/voshan/websocketService');
const { ingestPing } = require('./services/pingIngestService');

const authRoutes = require('./routes/authRoutes');
const adminRoutes = require('./routes/adminRoutes');
const deviceRoutes = require('./routes/deviceRoutes');
const alertRoutes = require('./routes/alertRoutes');
const riskRoutes = require('./routes/riskRoutes');
const storedItemRoutes = require('./routes/storedItemRoutes');
const calendarRoutes = require('./routes/calendarRoutes');
const reminderRoutes = require('./routes/reminderRoutes');
const bookingRoutes = require('./routes/bookingRoutes');
const monitoringRoutes = require('./routes/monitoringRoutes');
const locationRoutes = require('./routes/locationRoutes');
const csvUploadRoutes = require('./routes/csvUploadRoutes');
const zoneBookingRoutes = require('./routes/zoneBookingRoutes');
const mlTrainingRoutes = require('./routes/mlTrainingRoutes');
const voshanDetectionRoutes = require('./routes/voshan/detectionRoutes');

const app = express();

// Connect to MongoDB
connectDB();

// Middleware - Allow multiple origins for development (localhost + network IP)
const allowedOrigins = [
  'http://localhost:5173',
  'http://localhost:3000',
  env.FRONTEND_URL
];
app.use(cors({
  origin: function(origin, callback) {
    // Allow requests with no origin (mobile apps, curl, etc.)
    if (!origin) return callback(null, true);
    if (allowedOrigins.includes(origin) || origin.startsWith('http://192.168.')) {
      return callback(null, true);
    }
    return callback(null, true); // Allow all in development
  },
  credentials: true
}));
app.use(compression({
  filter: (req, res) => {
    if (req.path && req.path.startsWith('/api/voshan/socket.io')) return false;
    if (req.headers['x-no-compression']) return false;
    return compression.filter(req, res);
  },
  level: 6
}));
app.use(express.json({ limit: '500mb' }));
app.use(express.urlencoded({ extended: true, limit: '500mb' }));
app.use((req, res, next) => {
  res.setHeader('Connection', 'keep-alive');
  next();
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/devices', deviceRoutes);
app.use('/api/alerts', alertRoutes);
app.use('/api/risk', riskRoutes);
app.use('/api/stored-items', storedItemRoutes);
app.use('/api/calendar', calendarRoutes);
app.use('/api/reminders', reminderRoutes);
app.use('/api/bookings', bookingRoutes);
app.use('/api/monitoring', monitoringRoutes);
app.use('/api/location', locationRoutes);
app.use('/api/csv', csvUploadRoutes);
app.use('/api/zone-bookings', zoneBookingRoutes);
app.use('/api/ml-training', mlTrainingRoutes);

// Voshan: Serve captured alert frames
const alertFramesDir = path.resolve(__dirname, '../voshan/ml-service/outputs/alert_frames');
app.use('/api/voshan/detection/alert-frames', (req, res, next) => {
  res.setHeader('Cache-Control', 'no-cache, must-revalidate');
  next();
}, express.static(alertFramesDir));
// Voshan: Suspicious Behavior Detection
app.use('/api/voshan/detection', voshanDetectionRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// Check Python ML model on startup
async function initializeMLModel() {
  try {
    console.log('🤖 Checking Python ML Service...');
    const isAvailable = await pythonMLService.checkHealth();

    if (isAvailable) {
      const modelInfo = await pythonMLService.getModelInfo();
      console.log(`✅ Python ML Service Connected!`);
      console.log(`   🎯 Model Type: ${modelInfo?.model || 'XGBoost'}`);
      console.log(`   📊 Accuracy: ${((modelInfo?.metrics?.accuracy || 0) * 100).toFixed(2)}%`);
      console.log(`   📍 Service: http://localhost:5001`);
    } else {
      console.log('⚠️  Python ML Service not available');
      console.log('   Start it with: cd ml-service && python app.py');
    }
  } catch (error) {
    console.error('❌ ML Model Loading Failed:', error.message);
    console.log('⚠️  Server will continue without ML model');
  }
}

// Start server (HTTP + WebSocket)
const server = http.createServer(app);

// Voshan: Socket.IO for real-time detection alerts (path: /api/voshan/socket.io)
voshanWebsocketService.initialize(server);

// WebSocket hub
wsService.init(server, { path: '/ws' });
wsService.setOnPing(async (payload) => {
  // Optional ingest-key protection (since browsers can't set custom WS headers reliably)
  const requiredKey = process.env.DEVICE_INGEST_KEY;
  if (requiredKey && payload?.ingestKey !== requiredKey) {
    const err = new Error('Missing or invalid device ingest key');
    err.status = 401;
    throw err;
  }
  // Ingest using the exact same logic as HTTP
  const result = await ingestPing({ ...payload, source: 'ws' }, { source: 'ws' });
  wsService.broadcastPingSaved(result);
  return { ping: result.ping, deviceStatus: result.deviceStatus, zoneName: result.zoneName };
});

server.listen(env.PORT, async () => {
  console.log(`✅ Server running on port ${env.PORT}`);
  console.log(`📡 Environment: ${env.NODE_ENV}`);
  console.log('═══════════════════════════════════════════════════════════');

  // Voshan: init Supabase for alert storage (if SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY set)
  await initSupabase().catch(() => {});

  // Start reminder scheduler
  startScheduler();

  // Load Enhanced ML Ensemble model
  await initializeMLModel();

  console.log('═══════════════════════════════════════════════════════════');
  console.log('🚀 Academic ML System Ready!');
  console.log('📚 Ensemble Learning: Random Forest + Neural Network');
  console.log('═══════════════════════════════════════════════════════════');
});
