import { useState, useEffect, useCallback, useRef } from 'react';
import { API_BASE_URL } from '../api/config';

export const useWebSocket = (url = null) => {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const messageHandlers = useRef(new Map());

  const connect = useCallback((wsUrl) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const websocketUrl = wsUrl || url;
    if (!websocketUrl) return;

    try {
      ws.current = new WebSocket(websocketUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        
        // Clear reconnect timeout
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
          reconnectTimeout.current = null;
        }
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        
        // Call registered handlers
        messageHandlers.current.forEach((handler, key) => {
          handler(data);
        });
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(() => {
          connect(websocketUrl);
        }, 3000);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [url]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const send = useCallback((data) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  }, []);

  const subscribe = useCallback((key, handler) => {
    messageHandlers.current.set(key, handler);
  }, []);

  const unsubscribe = useCallback((key) => {
    messageHandlers.current.delete(key);
  }, []);

  useEffect(() => {
    if (url) {
      connect(url);
    }

    return () => {
      disconnect();
    };
  }, [url, connect, disconnect]);

  return {
    connected,
    lastMessage,
    send,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
  };
};

// Hook for processing WebSocket
export const useProcessingWebSocket = (processingId) => {
  const wsUrl = processingId 
    ? `${API_BASE_URL.replace('http', 'ws')}/ws/processing/${processingId}/`
    : null;
    
  return useWebSocket(wsUrl);
};

// Hook for validation WebSocket
export const useValidationWebSocket = () => {
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/validation/`;
  return useWebSocket(wsUrl);
};