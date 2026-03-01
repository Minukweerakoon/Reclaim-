const http = require('http');
const app = require('./src/app');
const dotenv = require('dotenv');
const connectDB = require('./src/config/database');
const websocketService = require('./src/services/voshan/websocketService');

// Load environment variables
dotenv.config();

const PORT = process.env.PORT || 5000;

// Create HTTP server
const server = http.createServer(app);

// Configure server timeouts for long-running requests (video processing)
server.timeout = parseInt(process.env.SERVER_TIMEOUT) || 1200000; // 20 minutes
server.keepAliveTimeout = 65000;
server.headersTimeout = 66000;

// Initialize WebSocket service
websocketService.initialize(server);

// Connect to database first, then start listening so alerts/DB routes don't buffer timeout
function startServer() {
  server.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
    console.log(`📡 WebSocket available at ws://localhost:${PORT}/api/voshan/socket.io`);
    console.log(`⏱️  Server timeout: ${server.timeout / 1000 / 60} minutes`);
  });
}

connectDB()
  .then(() => {
    startServer();
  })
  .catch((err) => {
    console.error('Database connection failed:', err.message);
    console.log('Starting server anyway - database features (e.g. alerts) will fail until MongoDB is available.');
    startServer();
  });

