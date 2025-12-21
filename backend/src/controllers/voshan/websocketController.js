/**
 * WebSocket Controller
 * Handles WebSocket-related requests and status
 */

const websocketService = require('../../services/voshan/websocketService');

/**
 * Get WebSocket connection status
 */
exports.getWebSocketStatus = async (req, res) => {
  try {
    const status = {
      enabled: websocketService.io !== null,
      connectedClients: websocketService.getConnectedCount(),
      clientIds: websocketService.getConnectedClients()
    };

    res.json({
      success: true,
      data: status
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error getting WebSocket status',
      error: error.message
    });
  }
};

