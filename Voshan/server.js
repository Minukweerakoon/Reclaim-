const http = require('http');
const app = require('./src/app');
const dotenv = require('dotenv');
const connectDB = require('./src/config/database');
const websocketService = require('./src/services/voshan/websocketService');

// Load environment variables
dotenv.config();

const PRIMARY_PORT = parseInt(process.env.PORT, 10) || 5000;
const FALLBACK_PORT = parseInt(process.env.PORT_FALLBACK, 10) || 5100;

// Create HTTP server
const server = http.createServer(app);

// Configure server timeouts for long-running requests (video processing)
server.timeout = parseInt(process.env.SERVER_TIMEOUT) || 1200000; // 20 minutes
server.keepAliveTimeout = 65000;
server.headersTimeout = 66000;

// Initialize WebSocket service
websocketService.initialize(server);

// Connect to database first, then start listening so alerts/DB routes don't buffer timeout
function startServer(port) {
  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      if (port === PRIMARY_PORT && FALLBACK_PORT !== PRIMARY_PORT) {
        console.warn(`\n⚠️ Port ${PRIMARY_PORT} is in use. Retrying on fallback port ${FALLBACK_PORT}...\n`);
        server.listen(FALLBACK_PORT);
        return;
      }
      console.error(`\n❌ Port ${port} is still in use. Set PORT in .env or free the port and retry.\n`);
    } else {
      console.error('Server error:', err);
    }
    process.exit(1);
  });
  server.listen(port, () => {
    const activePort = server.address() && typeof server.address() === 'object' ? server.address().port : port;
    console.log(`🚀 Server running on port ${activePort}`);
    console.log(`📡 WebSocket available at ws://localhost:${activePort}/api/voshan/socket.io`);
    console.log(`⏱️  Server timeout: ${server.timeout / 1000 / 60} minutes`);
  });
}

connectDB()
  .then(() => {
    startServer(PRIMARY_PORT);
  })
  .catch((err) => {
    console.error('Database connection failed:', err.message);
    console.log('Starting server anyway - database features (e.g. alerts) will fail until Supabase is configured.');
    startServer(PRIMARY_PORT);
  });

