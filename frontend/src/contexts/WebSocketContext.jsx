import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import io from 'socket.io-client';

const WebSocketContext = createContext(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const socketRef = useRef(null);
  const listenersRef = useRef(new Map());

  useEffect(() => {
    // Initialize WebSocket connection
    const socket = io(import.meta.env.VITE_WS_URL || 'ws://localhost:8001', {
      path: '/ws/socket.io',
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    // Connection event handlers
    socket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    // System-wide events
    socket.on('system:update', (data) => {
      setLastUpdate(data);
    });

    // Clean up on unmount
    return () => {
      socket.disconnect();
    };
  }, []);

  // Subscribe to events
  const subscribe = useCallback((event, callback) => {
    if (!socketRef.current) return;

    // Add listener
    socketRef.current.on(event, callback);

    // Track listeners for cleanup
    if (!listenersRef.current.has(event)) {
      listenersRef.current.set(event, new Set());
    }
    listenersRef.current.get(event).add(callback);

    // Return unsubscribe function
    return () => {
      if (socketRef.current) {
        socketRef.current.off(event, callback);
      }
      listenersRef.current.get(event)?.delete(callback);
    };
  }, []);

  // Emit events
  const emit = useCallback((event, data) => {
    if (!socketRef.current || !isConnected) {
      console.warn('WebSocket not connected, queueing event:', event);
      return;
    }
    socketRef.current.emit(event, data);
  }, [isConnected]);

  // Join/leave rooms
  const joinRoom = useCallback((room) => {
    emit('join:room', { room });
  }, [emit]);

  const leaveRoom = useCallback((room) => {
    emit('leave:room', { room });
  }, [emit]);

  const value = {
    isConnected,
    lastUpdate,
    subscribe,
    emit,
    joinRoom,
    leaveRoom,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};