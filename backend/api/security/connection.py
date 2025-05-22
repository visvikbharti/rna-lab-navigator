"""
Connection security utilities for RNA Lab Navigator.
This module provides connection timeout, automatic termination, and related security features.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable
from django.conf import settings
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

# Connection activity tracker
connection_trackers = {}
connection_lock = threading.Lock()


class ConnectionTracker:
    """
    Tracks activity on a connection and terminates inactive connections.
    """
    
    def __init__(self, session_id: str, timeout_seconds: int = 1800):
        """Initialize connection tracker"""
        self.session_id = session_id
        self.last_activity = time.time()
        self.timeout_seconds = timeout_seconds
        self.is_active = True
        self.total_requests = 0
        self.start_time = time.time()
        
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = time.time()
        self.total_requests += 1
        
    def check_timeout(self) -> bool:
        """
        Check if the connection has timed out.
        
        Returns:
            bool: True if connection has timed out
        """
        if not self.is_active:
            return True
            
        elapsed = time.time() - self.last_activity
        return elapsed > self.timeout_seconds
        
    def terminate(self):
        """Mark the connection as terminated"""
        self.is_active = False
        logger.info(f"Terminated connection for session {self.session_id} "
                   f"after {self.total_requests} requests and "
                   f"{time.time() - self.start_time:.1f} seconds")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "last_activity": self.last_activity,
            "total_requests": self.total_requests,
            "session_duration": time.time() - self.start_time,
            "idle_time": time.time() - self.last_activity
        }


def get_or_create_tracker(session_id: str) -> ConnectionTracker:
    """
    Get or create a connection tracker for the given session ID.
    Thread-safe with locking.
    
    Args:
        session_id: Session ID
        
    Returns:
        ConnectionTracker: Tracker for the session
    """
    with connection_lock:
        if session_id in connection_trackers:
            tracker = connection_trackers[session_id]
            
            # If terminated, create a new one
            if not tracker.is_active:
                tracker = ConnectionTracker(
                    session_id,
                    timeout_seconds=getattr(settings, 'CONNECTION_TIMEOUT_SECONDS', 1800)
                )
                connection_trackers[session_id] = tracker
                
            return tracker
        else:
            # Create new tracker
            tracker = ConnectionTracker(
                session_id,
                timeout_seconds=getattr(settings, 'CONNECTION_TIMEOUT_SECONDS', 1800)
            )
            connection_trackers[session_id] = tracker
            return tracker


def cleanup_connections():
    """
    Cleanup expired connections.
    Should be called periodically by a background task.
    """
    with connection_lock:
        current_time = time.time()
        expired_sessions = []
        
        for session_id, tracker in connection_trackers.items():
            if tracker.check_timeout():
                tracker.terminate()
                expired_sessions.append(session_id)
                
        # Remove terminated trackers
        for session_id in expired_sessions:
            del connection_trackers[session_id]
            
        logger.info(f"Cleaned up {len(expired_sessions)} expired connections. "
                   f"Active connections: {len(connection_trackers)}")


def start_cleanup_thread(interval_seconds: int = 300):
    """
    Start a background thread to periodically clean up expired connections.
    
    Args:
        interval_seconds: Interval between cleanup runs
    """
    def cleanup_thread():
        while True:
            time.sleep(interval_seconds)
            try:
                cleanup_connections()
            except Exception as e:
                logger.error(f"Error in connection cleanup thread: {e}")
                
    thread = threading.Thread(target=cleanup_thread, daemon=True)
    thread.start()
    logger.info(f"Started connection cleanup thread with interval {interval_seconds} seconds")


class ConnectionTimeoutMiddleware:
    """
    Middleware that enforces connection timeouts and tracks activity.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Start cleanup thread if enabled
        if getattr(settings, 'ENABLE_CONNECTION_TIMEOUT', False):
            cleanup_interval = getattr(settings, 'CONNECTION_CLEANUP_INTERVAL', 300)
            start_cleanup_thread(cleanup_interval)
        
    def __call__(self, request):
        if not getattr(settings, 'ENABLE_CONNECTION_TIMEOUT', False):
            return self.get_response(request)
            
        # Get session ID
        session_id = request.session.session_key
        if not session_id:
            # No session, proceed without tracking
            return self.get_response(request)
            
        # Get tracker
        tracker = get_or_create_tracker(session_id)
        
        # Check if connection has timed out
        if tracker.check_timeout():
            tracker.terminate()
            
            # Clear session and return timeout response
            request.session.flush()
            
            from django.http import JsonResponse
            return JsonResponse({
                "error": "Session timeout",
                "detail": "Your session has expired due to inactivity."
            }, status=401)
            
        # Update activity
        tracker.update_activity()
        
        # Process request
        response = self.get_response(request)
        
        # Add timeout header
        timeout_seconds = getattr(settings, 'CONNECTION_TIMEOUT_SECONDS', 1800)
        remaining = int(timeout_seconds - (time.time() - tracker.last_activity))
        response['X-Session-Timeout-In'] = str(remaining)
        
        return response