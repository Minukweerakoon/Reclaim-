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
    const cors = require('cors');

    this.io = new Server(server, {
      cors: {
        origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
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
      console.log(`📡 Client connected: ${clientId} (Total: ${this.connectedClients.size})`);

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

    // Broadcast to all clients subscribed to alerts
    this.io.to('alerts').emit('new-alert', alert);
    console.log(`📢 Broadcasted alert: ${alert.type} (ID: ${alert.alertId})`);

    // Also broadcast to specific camera room if cameraId exists
    if (alert.cameraId) {
      this.io.to(`camera-${alert.cameraId}`).emit('new-alert', alert);
      console.log(`📹 Broadcasted alert to camera room: ${alert.cameraId}`);
    }
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

