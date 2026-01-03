/**
 * WebSocket Hook
 * Manages WebSocket connection for real-time alerts
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';

// Construct WebSocket URL properly
const getSocketUrl = () => {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
  // Remove /api suffix if present, or use base URL
  if (apiUrl.endsWith('/api')) {
    return apiUrl.replace('/api', '');
  }
  return apiUrl.replace(/\/api\/?$/, '') || 'http://localhost:5000';
};

const SOCKET_URL = getSocketUrl();
const SOCKET_PATH = '/api/voshan/socket.io';

export const useWebSocket = (options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [connectionError, setConnectionError] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const { cameraId, autoConnect = true } = options;

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Disconnect existing connection if any
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      console.log(`🔌 Connecting to WebSocket: ${SOCKET_URL}${SOCKET_PATH}`);
      
      const socket = io(SOCKET_URL, {
        path: SOCKET_PATH,
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: Infinity, // Keep trying to reconnect
        timeout: 20000,
        forceNew: true, // Force new connection
      });

      socket.on('connect', () => {
        console.log('✅ WebSocket connected:', socket.id);
        setIsConnected(true);
        setConnectionError(null);

        // Subscribe to all alerts
        socket.emit('subscribe-alerts');

        // Join camera room if cameraId provided
        if (cameraId) {
          socket.emit('join-camera', cameraId);
        }
      });

      socket.on('disconnect', (reason) => {
        console.log('❌ WebSocket disconnected:', reason);
        setIsConnected(false);
        
        // Auto-reconnect if not manually disconnected
        if (reason === 'io server disconnect') {
          // Server disconnected, reconnect manually
          socket.connect();
        }
      });

      socket.on('connect_error', (error) => {
        console.error('❌ WebSocket connection error:', error.message);
        setConnectionError(error.message);
        setIsConnected(false);
        
        // Log connection details for debugging
        console.error('Connection details:', {
          url: SOCKET_URL,
          path: SOCKET_PATH,
          fullUrl: `${SOCKET_URL}${SOCKET_PATH}`,
          error: error.message
        });
      });

      socket.on('new-alert', (alert) => {
        console.log('📢 New alert received:', alert);
        setAlerts((prev) => [alert, ...prev]);
        
        // Call custom alert handler if provided
        if (options.onAlert) {
          options.onAlert(alert);
        }
      });

      socket.on('joined-camera', (data) => {
        console.log('📹 Joined camera room:', data.cameraId);
      });

      socket.on('subscribed-alerts', (data) => {
        console.log('🔔 Subscribed to alerts:', data.success);
      });

      socket.on('pong', (data) => {
        console.log('🏓 Pong received:', data.timestamp);
      });

      socket.on('reconnect', (attemptNumber) => {
        console.log(`🔄 WebSocket reconnected after ${attemptNumber} attempts`);
        setIsConnected(true);
        setConnectionError(null);
        // Re-subscribe after reconnection
        socket.emit('subscribe-alerts');
        if (cameraId) {
          socket.emit('join-camera', cameraId);
        }
      });

      socket.on('reconnect_attempt', (attemptNumber) => {
        console.log(`🔄 Reconnection attempt ${attemptNumber}...`);
      });

      socket.on('reconnect_error', (error) => {
        console.error('❌ Reconnection error:', error.message);
        setConnectionError(`Reconnection failed: ${error.message}`);
      });

      socket.on('reconnect_failed', () => {
        console.error('❌ WebSocket reconnection failed after all attempts');
        setConnectionError('Failed to reconnect. Please refresh the page.');
      });

      socketRef.current = socket;
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setConnectionError(error.message);
      
      // Retry connection after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('🔄 Retrying WebSocket connection...');
        connect();
      }, 5000);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cameraId]); // Only depend on cameraId, options handled via closure

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
      setAlerts([]);
      console.log('🔌 WebSocket manually disconnected');
    }
  }, []);

  // Join camera room
  const joinCamera = useCallback((cameraId) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('join-camera', cameraId);
    }
  }, []);

  // Leave camera room
  const leaveCamera = useCallback((cameraId) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('leave-camera', cameraId);
    }
  }, []);

  // Clear alerts
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (!autoConnect) {
      return;
    }

    // Connect when component mounts
    connect();

    // Cleanup: disconnect when component unmounts
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
      setIsConnected(false);
      setAlerts([]);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]); // Only depend on autoConnect, not connect/disconnect functions

  return {
    isConnected,
    alerts,
    connectionError,
    connect,
    disconnect,
    joinCamera,
    leaveCamera,
    clearAlerts,
    socket: socketRef.current,
  };
};

export default useWebSocket;

