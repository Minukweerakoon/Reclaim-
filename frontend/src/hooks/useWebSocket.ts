import { useState, useEffect, useRef, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export const useWebSocket = (url: string = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/validation') => {
  const [wsConnected, setWsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const clientIdRef = useRef<string>(`${Date.now()}-${Math.random().toString(36).slice(2)}`);

  const connect = useCallback(() => {
    // Ensure URL contains required client_id suffix
    const finalUrl = url.endsWith(clientIdRef.current)
      ? url
      : `${url.replace(/\/$/, '')}/${clientIdRef.current}`;
    ws.current = new WebSocket(finalUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
    };

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
      // Attempt to reconnect after a delay
      setTimeout(connect, 3000);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      ws.current?.close();
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not open. Message not sent:', message);
    }
  }, []);

  return { wsConnected, lastMessage, sendMessage };
};