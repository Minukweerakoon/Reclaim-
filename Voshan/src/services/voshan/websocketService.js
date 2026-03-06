/**
 * WebSocket Service
 * Manages WebSocket connections for real-time alert broadcasting
 */

class WebSocketService {
  constructor() {
    this.io = null;
    this.connectedClients = new Map(); // clientId -> socket
  }

  /**
   * Initialize WebSocket server
   * @param {Object} server - HTTP server instance
   */
  initialize(server) {
    const { Server } = require('socket.io');

    // Allow multiple origins so both localhost and 127.0.0.1 work
    const allowedOrigins = [
      'http://localhost:3000',
      'http://127.0.0.1:3000',
      'http://localhost:5173',
      'http://127.0.0.1:5173'
    ];
    if (process.env.CORS_ORIGIN && !allowedOrigins.includes(process.env.CORS_ORIGIN)) {
      allowedOrigins.push(process.env.CORS_ORIGIN);
    }

    this.io = new Server(server, {
      cors: {
        origin: allowedOrigins,
        methods: ['GET', 'POST'],
        credentials: true
      },
      path: '/api/voshan/socket.io'
    });

    this.setupEventHandlers();
    console.log('✅ WebSocket service initialized for Voshan detection');
  }

  /**
   * Setup WebSocket event handlers
   */
  setupEventHandlers() {
    this.io.on('connection', (socket) => {
      const clientId = socket.id;
      this.connectedClients.set(clientId, socket);
      socket.join('alerts');
      console.log(`📡 Client connected: ${clientId} (Total: ${this.connectedClients.size}) [auto-joined alerts]`);

      // Handle client joining camera room
      socket.on('join-camera', (cameraId) => {
        socket.join(`camera-${cameraId}`);
        console.log(`📹 Client ${clientId} joined camera room: ${cameraId}`);
        socket.emit('joined-camera', { cameraId });
      });

      // Handle client leaving camera room
      socket.on('leave-camera', (cameraId) => {
        socket.leave(`camera-${cameraId}`);
        console.log(`📹 Client ${clientId} left camera room: ${cameraId}`);
      });

      // Handle client subscribing to all alerts
      socket.on('subscribe-alerts', () => {
        socket.join('alerts');
        console.log(`🔔 Client ${clientId} subscribed to all alerts`);
        socket.emit('subscribed-alerts', { success: true });
      });

      // Handle client unsubscribing from alerts
      socket.on('unsubscribe-alerts', () => {
        socket.leave('alerts');
        console.log(`🔕 Client ${clientId} unsubscribed from alerts`);
      });

      // Handle ping/pong for connection health
      socket.on('ping', () => {
        socket.emit('pong', { timestamp: Date.now() });
      });

      // Handle disconnection
      socket.on('disconnect', () => {
        this.connectedClients.delete(clientId);
        console.log(`📴 Client disconnected: ${clientId} (Total: ${this.connectedClients.size})`);
      });
    });
  }

  /**
   * Broadcast alert to all connected clients
   * @param {Object} alert - Alert object
   */
  broadcastAlert(alert) {
    if (!this.io) {
      console.warn('⚠️ WebSocket not initialized, cannot broadcast alert');
      return;
    }

    // Get room sizes for debugging
    const alertsRoom = this.io.sockets.adapter.rooms.get('alerts');
    const alertsRoomSize = alertsRoom ? alertsRoom.size : 0;

    // Broadcast to all clients subscribed to alerts
    this.io.to('alerts').emit('new-alert', alert);
    console.log(`📢 Broadcasted alert: ${alert.type} (ID: ${alert.alertId}) to ${alertsRoomSize} client(s) in alerts room`);

    // Also broadcast to specific camera room if cameraId exists
    if (alert.cameraId) {
      const cameraRoom = this.io.sockets.adapter.rooms.get(`camera-${alert.cameraId}`);
      const cameraRoomSize = cameraRoom ? cameraRoom.size : 0;
      this.io.to(`camera-${alert.cameraId}`).emit('new-alert', alert);
      console.log(`📹 Broadcasted alert to camera room: ${alert.cameraId} (${cameraRoomSize} client(s))`);
    }
  }

  /**
   * Broadcast a grouped alert (e.g. N alerts of same type in a 50-frame window)
   * @param {Object} group - { type, count, frameStart, frameEnd, cameraId, severity, frameImages[] }
   */
  broadcastAlertGroup(group) {
    if (!this.io) {
      console.warn('⚠️ WebSocket not initialized, cannot broadcast grouped alert');
      return;
    }
    const alertsRoom = this.io.sockets.adapter.rooms.get('alerts');
    const alertsRoomSize = alertsRoom ? alertsRoom.size : 0;
    this.io.to('alerts').emit('grouped-alert', group);
    if (group.cameraId) {
      this.io.to(`camera-${group.cameraId}`).emit('grouped-alert', group);
    }
    console.log(`📢 Broadcasted grouped alert: ${group.count}× ${group.type} (frames ${group.frameStart}-${group.frameEnd}) to ${alertsRoomSize} client(s)`);
  }

  /**
   * Broadcast alert to specific camera room
   * @param {String} cameraId - Camera identifier
   * @param {Object} alert - Alert object
   */
  broadcastToCamera(cameraId, alert) {
    if (!this.io) {
      console.warn('⚠️ WebSocket not initialized, cannot broadcast alert');
      return;
    }

    this.io.to(`camera-${cameraId}`).emit('new-alert', alert);
    console.log(`📹 Broadcasted alert to camera ${cameraId}: ${alert.type}`);
  }

  /**
   * Send alert to specific client
   * @param {String} clientId - Client socket ID
   * @param {Object} alert - Alert object
   */
  sendToClient(clientId, alert) {
    if (!this.io) {
      console.warn('⚠️ WebSocket not initialized, cannot send alert');
      return;
    }

    const socket = this.connectedClients.get(clientId);
    if (socket) {
      socket.emit('new-alert', alert);
      console.log(`📤 Sent alert to client ${clientId}: ${alert.type}`);
    } else {
      console.warn(`⚠️ Client ${clientId} not found`);
    }
  }

  /**
   * Broadcast detection status update
   * @param {Object} status - Status object
   */
  broadcastStatus(status) {
    if (!this.io) {
      return;
    }

    this.io.emit('detection-status', status);
  }

  /**
   * Get connected clients count
   * @returns {Number} Number of connected clients
   */
  getConnectedCount() {
    return this.connectedClients.size;
  }

  /**
   * Get all connected client IDs
   * @returns {Array} Array of client IDs
   */
  getConnectedClients() {
    return Array.from(this.connectedClients.keys());
  }
}

module.exports = new WebSocketService();

