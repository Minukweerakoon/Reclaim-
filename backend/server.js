const http = require('http');
const app = require('./src/app');
const dotenv = require('dotenv');
const connectDB = require('./src/config/database');
const websocketService = require('./src/services/voshan/websocketService');

// Load environment variables
dotenv.config();

const PORT = process.env.PORT || 5000;

// Connect to database (non-blocking - server will start even if DB fails)
connectDB().catch((err) => {
  console.error('Database connection failed, but server will continue...');
});

// Create HTTP server
const server = http.createServer(app);

// Initialize WebSocket service
websocketService.initialize(server);

// Start server
server.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📡 WebSocket available at ws://localhost:${PORT}/api/voshan/socket.io`);
});

