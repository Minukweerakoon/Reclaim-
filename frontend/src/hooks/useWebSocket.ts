import { useEffect, useRef, useState, useCallback } from 'react';
import type { WSProgressMessage } from '../types/api';

interface UseWebSocketOptions {
    clientId: string;
    onMessage?: (message: WSProgressMessage) => void;
    onError?: (error: string) => void;
    autoReconnect?: boolean;
    maxRetries?: number;
    heartbeatInterval?: number;
}

export function useWebSocket({ 
    clientId, 
    onMessage, 
    onError, 
    autoReconnect = true,
    maxRetries = 3,
    heartbeatInterval = 30000 // Send heartbeat every 30s to keep connection alive
}: UseWebSocketOptions) {
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const heartbeatTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const retriesRef = useRef(0);
    const maxRetriesRef = useRef(maxRetries);
    const manualCloseRef = useRef(false);
    const shouldReconnectRef = useRef(autoReconnect);
    const attemptIdRef = useRef(0);

    const onMessageRef = useRef(onMessage);
    const onErrorRef = useRef(onError);

    useEffect(() => {
        onMessageRef.current = onMessage;
        onErrorRef.current = onError;
    }, [onMessage, onError]);

    const sendHeartbeat = useCallback(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            try {
                wsRef.current.send(JSON.stringify({ type: 'ping' }));
                console.log('[WebSocket] Heartbeat sent');
            } catch (err) {
                console.error('[WebSocket] Failed to send heartbeat:', err);
            }
        }
    }, []);

    const scheduleHeartbeat = useCallback(() => {
        if (heartbeatTimeoutRef.current) {
            clearTimeout(heartbeatTimeoutRef.current);
        }
        heartbeatTimeoutRef.current = setTimeout(() => {
            sendHeartbeat();
            scheduleHeartbeat();
        }, heartbeatInterval);
    }, [heartbeatInterval, sendHeartbeat]);

    const connect = useCallback(() => {
        if (wsRef.current) {
            console.log('[WebSocket] Already connecting or connected');
            return;
        }

        manualCloseRef.current = false;
        shouldReconnectRef.current = autoReconnect;
        attemptIdRef.current += 1;
        const attemptId = attemptIdRef.current;

        try {
            // Build WebSocket URL - connect directly to backend server
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = import.meta.env.DEV 
                ? '127.0.0.1:8000' // In dev, connect directly to backend
                : window.location.host; // In prod, same origin
            const wsUrl = `${protocol}//${host}/ws/validation/${clientId}`;

            console.log('[WebSocket] Connecting to:', wsUrl, '(attempt', retriesRef.current + 1, ')');
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            // Connection timeout safety net
            const timeoutHandle = setTimeout(() => {
                if (ws.readyState === WebSocket.CONNECTING) {
                    console.warn('[WebSocket] Connection timeout (>8s), closing');
                    manualCloseRef.current = true;
                    ws.close();
                }
            }, 8000);

            ws.onopen = () => {
                clearTimeout(timeoutHandle);
                if (attemptId !== attemptIdRef.current) {
                    return;
                }
                console.log('[WebSocket] Connected successfully');
                setIsConnected(true);
                retriesRef.current = 0; // Reset retries on successful connection
                scheduleHeartbeat(); // Start sending heartbeats
            };

            ws.onmessage = (event) => {
                if (attemptId !== attemptIdRef.current) {
                    return;
                }
                try {
                    const rawMessage = JSON.parse(event.data) as WSProgressMessage;
                    const message: WSProgressMessage = {
                        ...rawMessage,
                        type: rawMessage.type || (rawMessage.status === 'connected' ? 'connected' : undefined),
                    };
                    // Ignore pong responses
                    if (message.type === 'pong') {
                        console.log('[WebSocket] Pong received');
                        return;
                    }

                    if (!message.type) {
                        console.log('[WebSocket] Message received with unknown type:', rawMessage);
                        return;
                    }

                    console.log('[WebSocket] Message received:', message.type);
                    onMessageRef.current?.(message);
                } catch (err) {
                    console.error('[WebSocket] Failed to parse message:', event.data, err);
                }
            };

            ws.onerror = (event) => {
                clearTimeout(timeoutHandle);
                if (manualCloseRef.current || attemptId !== attemptIdRef.current) {
                    return;
                }
                if (ws.readyState === WebSocket.CLOSING || ws.readyState === WebSocket.CLOSED) {
                    return;
                }
                const errorMsg = `WebSocket error: ${event instanceof Event ? event.type : 'unknown'}`;
                console.error('[WebSocket] Error:', errorMsg);
                onErrorRef.current?.(errorMsg);
            };

            ws.onclose = (event) => {
                clearTimeout(timeoutHandle);
                if (heartbeatTimeoutRef.current) {
                    clearTimeout(heartbeatTimeoutRef.current);
                }
                if (manualCloseRef.current || attemptId !== attemptIdRef.current) {
                    setIsConnected(false);
                    wsRef.current = null;
                    return;
                }
                console.log('[WebSocket] Connection closed', { code: event.code, reason: event.reason, wasClean: event.wasClean });
                setIsConnected(false);
                wsRef.current = null;

                // Auto reconnect with exponential backoff
                if (shouldReconnectRef.current && retriesRef.current < maxRetriesRef.current) {
                    const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000); // Max 30s
                    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${retriesRef.current + 1}/${maxRetriesRef.current})`);
                    retriesRef.current++;
                    
                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, delay);
                } else if (retriesRef.current >= maxRetriesRef.current) {
                    const failMsg = `WebSocket failed after ${maxRetriesRef.current} attempts. Using polling for updates.`;
                    console.warn('[WebSocket]', failMsg);
                    onErrorRef.current?.(failMsg);
                }
            };
        } catch (err) {
            const errorMsg = `[WebSocket] Connection failed: ${err instanceof Error ? err.message : String(err)}`;
            console.error(errorMsg);
            onErrorRef.current?.(errorMsg);
        }
    }, [clientId, autoReconnect, maxRetries, scheduleHeartbeat]);

    const disconnect = useCallback(() => {
        manualCloseRef.current = true;
        shouldReconnectRef.current = false;
        attemptIdRef.current += 1;
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        if (heartbeatTimeoutRef.current) {
            clearTimeout(heartbeatTimeoutRef.current);
            heartbeatTimeoutRef.current = null;
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setIsConnected(false);
    }, []);

    const sendMessage = useCallback((message: any) => {
        if (wsRef.current && isConnected && wsRef.current.readyState === WebSocket.OPEN) {
            try {
                wsRef.current.send(JSON.stringify(message));
                console.log('[WebSocket] Message sent:', message.type || 'unknown');
            } catch (err) {
                console.error('[WebSocket] Failed to send message:', err);
            }
        } else {
            console.warn('[WebSocket] Cannot send message:', {
                hasWs: !!wsRef.current,
                isConnected,
                readyState: wsRef.current?.readyState
            });
        }
    }, [isConnected]);

    useEffect(() => {
        // Delay connection slightly so React StrictMode's immediate
        // unmount/remount cycle never creates (then immediately destroys)
        // a WebSocket — which causes the browser-level
        // "WebSocket is closed before the connection is established" warning.
        const timer = setTimeout(() => {
            connect();
        }, 150);
        return () => {
            clearTimeout(timer);
            disconnect();
        };
    }, [connect, disconnect]);

    return {
        isConnected,
        sendMessage,
        disconnect,
        reconnect: connect,
    };
}
