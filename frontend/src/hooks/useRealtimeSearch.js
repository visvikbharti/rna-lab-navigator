import { useEffect, useState, useCallback } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useQueryClient } from '@tanstack/react-query';

export function useRealtimeSearch(sessionId) {
  const { subscribe, emit, joinRoom, leaveRoom, isConnected } = useWebSocket();
  const queryClient = useQueryClient();
  const [realtimeUpdates, setRealtimeUpdates] = useState([]);

  useEffect(() => {
    if (!sessionId || !isConnected) return;

    // Join session room
    joinRoom(`search:${sessionId}`);

    // Subscribe to search updates
    const unsubscribeProgress = subscribe('search:progress', (data) => {
      if (data.sessionId === sessionId) {
        setRealtimeUpdates(prev => [...prev, {
          type: 'progress',
          timestamp: Date.now(),
          ...data
        }]);
      }
    });

    const unsubscribeComplete = subscribe('search:complete', (data) => {
      if (data.sessionId === sessionId) {
        // Invalidate and refetch the search query
        queryClient.invalidateQueries(['search']);
        setRealtimeUpdates(prev => [...prev, {
          type: 'complete',
          timestamp: Date.now(),
          ...data
        }]);
      }
    });

    const unsubscribeNewResult = subscribe('search:new-result', (data) => {
      if (data.sessionId === sessionId) {
        // Update cache with new result
        queryClient.setQueryData(['search', data.query], (oldData) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            results: [...(oldData.results || []), data.result]
          };
        });
      }
    });

    // Cleanup
    return () => {
      leaveRoom(`search:${sessionId}`);
      unsubscribeProgress();
      unsubscribeComplete();
      unsubscribeNewResult();
    };
  }, [sessionId, isConnected, subscribe, joinRoom, leaveRoom, queryClient]);

  // Send search analytics
  const sendAnalytics = useCallback((event, data) => {
    emit('search:analytics', {
      sessionId,
      event,
      timestamp: Date.now(),
      ...data
    });
  }, [emit, sessionId]);

  return {
    realtimeUpdates,
    sendAnalytics,
    isConnected
  };
}

// Hook for real-time collaboration features
export function useRealtimeCollaboration(documentId) {
  const { subscribe, emit, joinRoom, leaveRoom, isConnected } = useWebSocket();
  const [activeUsers, setActiveUsers] = useState([]);
  const [cursorPositions, setCursorPositions] = useState({});

  useEffect(() => {
    if (!documentId || !isConnected) return;

    // Join document room
    joinRoom(`doc:${documentId}`);

    // Subscribe to user presence
    const unsubscribeUserJoin = subscribe('doc:user-join', (data) => {
      if (data.documentId === documentId) {
        setActiveUsers(prev => [...prev, data.user]);
      }
    });

    const unsubscribeUserLeave = subscribe('doc:user-leave', (data) => {
      if (data.documentId === documentId) {
        setActiveUsers(prev => prev.filter(u => u.id !== data.userId));
        setCursorPositions(prev => {
          const newPositions = { ...prev };
          delete newPositions[data.userId];
          return newPositions;
        });
      }
    });

    const unsubscribeCursorMove = subscribe('doc:cursor-move', (data) => {
      if (data.documentId === documentId) {
        setCursorPositions(prev => ({
          ...prev,
          [data.userId]: data.position
        }));
      }
    });

    // Cleanup
    return () => {
      leaveRoom(`doc:${documentId}`);
      unsubscribeUserJoin();
      unsubscribeUserLeave();
      unsubscribeCursorMove();
    };
  }, [documentId, isConnected, subscribe, joinRoom, leaveRoom]);

  // Send cursor position
  const sendCursorPosition = useCallback((position) => {
    emit('doc:cursor-move', {
      documentId,
      position
    });
  }, [emit, documentId]);

  return {
    activeUsers,
    cursorPositions,
    sendCursorPosition,
    isConnected
  };
}

// Hook for real-time notifications
export function useRealtimeNotifications() {
  const { subscribe, isConnected } = useWebSocket();
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    if (!isConnected) return;

    const unsubscribe = subscribe('notification', (data) => {
      setNotifications(prev => [{
        id: Date.now(),
        timestamp: new Date(),
        ...data
      }, ...prev].slice(0, 50)); // Keep last 50 notifications
    });

    return unsubscribe;
  }, [isConnected, subscribe]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    clearNotifications
  };
}