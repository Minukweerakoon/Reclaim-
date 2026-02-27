/**
 * WebSocket Hook
 * Manages WebSocket connection for real-time alerts
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:5000';
const SOCKET_PATH = '/api/voshan/socket.io';

export const useWebSocket = (options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [connectionError, setConnectionError] = useState(null);
  const socketRef = useRef(null);
  const { cameraId, autoConnect = true } = options;

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    try {
      const socket = io(SOCKET_URL, {
        path: SOCKET_PATH,
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
      });

      socket.on('connect', () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);

        // Subscribe to all alerts
        socket.emit('subscribe-alerts');

        // Join camera room if cameraId provided
        if (cameraId) {
          socket.emit('join-camera', cameraId);
        }
      });

      socket.on('disconnect', () => {
        console.log('❌ WebSocket disconnected');
        setIsConnected(false);
      });

      socket.on('connect_error', (error) => {
        console.error('❌ WebSocket connection error:', error);
        setConnectionError(error.message);
        setIsConnected(false);
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

      socketRef.current = socket;
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setConnectionError(error.message);
    }
  }, [cameraId, options]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
      setAlerts([]);
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
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

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

