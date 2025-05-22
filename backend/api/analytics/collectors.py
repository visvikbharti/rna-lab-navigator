"""
Data collectors for analytics system.
These collectors are responsible for capturing and storing analytics data.
"""

import time
import json
import re
import logging
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User, AnonymousUser

from .models import (
    SystemMetric,
    AuditEvent,
    UserActivityLog,
    SecurityEvent
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and stores metrics about system performance and usage.
    Provides methods for recording various types of metrics.
    """
    
    @classmethod
    def record_response_time(cls, path, method, user_id, status_code, time_ms, metadata=None):
        """
        Record API response time metric.
        
        Args:
            path: Request path
            method: HTTP method
            user_id: User ID or None
            status_code: HTTP status code
            time_ms: Response time in milliseconds
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        metadata.update({
            'path': path,
            'method': method,
            'status_code': status_code,
            'user_id': user_id,
        })
        
        try:
            SystemMetric.objects.create(
                metric_type='response_time',
                value=time_ms,
                unit='ms',
                metadata=metadata
            )
            return True
        except Exception as e:
            logger.error(f"Error recording response time metric: {str(e)}")
            return False

    @classmethod
    def record_query_latency(cls, query_type, latency_ms, user_id=None, metadata=None):
        """
        Record query processing latency.
        
        Args:
            query_type: Type of query (vector, full-text, hybrid)
            latency_ms: Processing time in milliseconds
            user_id: User ID or None
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        metadata.update({
            'user_id': user_id,
            'query_type': query_type,
        })
        
        try:
            SystemMetric.objects.create(
                metric_type='query_latency',
                value=latency_ms,
                unit='ms',
                metadata=metadata
            )
            return True
        except Exception as e:
            logger.error(f"Error recording query latency metric: {str(e)}")
            return False
    
    @classmethod
    def record_llm_generation_time(cls, model, prompt_tokens, completion_tokens, time_ms, metadata=None):
        """
        Record LLM generation time metric.
        
        Args:
            model: LLM model name (e.g., gpt-4o)
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            time_ms: Generation time in milliseconds
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        metadata.update({
            'model': model,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
        })
        
        try:
            SystemMetric.objects.create(
                metric_type='llm_generation_time',
                value=time_ms,
                unit='ms',
                metadata=metadata
            )
            return True
        except Exception as e:
            logger.error(f"Error recording LLM generation time metric: {str(e)}")
            return False
    
    @classmethod
    def record_vector_search_time(cls, collection, num_vectors, top_k, time_ms, metadata=None):
        """
        Record vector search time metric.
        
        Args:
            collection: Vector collection name
            num_vectors: Number of vectors in collection
            top_k: Number of results requested
            time_ms: Search time in milliseconds
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        metadata.update({
            'collection': collection,
            'num_vectors': num_vectors,
            'top_k': top_k,
        })
        
        try:
            SystemMetric.objects.create(
                metric_type='vector_search_time',
                value=time_ms,
                unit='ms',
                metadata=metadata
            )
            return True
        except Exception as e:
            logger.error(f"Error recording vector search time metric: {str(e)}")
            return False
    
    @classmethod
    def record_system_metrics(cls):
        """
        Record current system metrics (CPU, memory, disk usage).
        Requires psutil to be installed.
        """
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SystemMetric.objects.create(
                metric_type='cpu_usage',
                value=cpu_percent,
                unit='%'
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            SystemMetric.objects.create(
                metric_type='memory_usage',
                value=memory.percent,
                unit='%',
                metadata={
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                }
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            SystemMetric.objects.create(
                metric_type='disk_usage',
                value=disk.percent,
                unit='%',
                metadata={
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                }
            )
            
            return True
        except ImportError:
            logger.warning("psutil not installed, skipping system metrics collection")
            return False
        except Exception as e:
            logger.error(f"Error recording system metrics: {str(e)}")
            return False


class ActivityCollector:
    """
    Collects and stores user activity data.
    Provides methods for recording various types of user activities.
    """
    
    @classmethod
    def record_user_activity(cls, user, activity_type, ip_address=None, session_id=None, 
                            resource_id=None, resource_type=None, status="success", metadata=None):
        """
        Record user activity.
        
        Args:
            user: User object or None for anonymous users
            activity_type: Type of activity (see UserActivityLog.ACTIVITY_TYPES)
            ip_address: User's IP address (optional)
            session_id: Session ID (optional)
            resource_id: ID of the accessed resource (optional)
            resource_type: Type of the accessed resource (optional)
            status: Status of the activity (success, failure)
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        
        try:
            # Don't store user object for anonymous users
            user_obj = None if isinstance(user, AnonymousUser) else user
            
            UserActivityLog.objects.create(
                user=user_obj,
                activity_type=activity_type,
                timestamp=timezone.now(),
                ip_address=ip_address,
                session_id=session_id,
                resource_id=resource_id,
                resource_type=resource_type,
                status=status,
                metadata=metadata
            )
            return True
        except Exception as e:
            logger.error(f"Error recording user activity: {str(e)}")
            return False
    
    @classmethod
    def record_query(cls, user, query_text, response_time=None, ip_address=None, 
                    session_id=None, success=True, confidence_score=None, metadata=None):
        """
        Record a user query.
        
        Args:
            user: User object or None for anonymous users
            query_text: The query text
            response_time: Response time in ms (optional)
            ip_address: User's IP address (optional)
            session_id: Session ID (optional)
            success: Whether the query was successful
            confidence_score: Confidence score of the answer (optional)
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        metadata.update({
            'query_text': query_text,
            'response_time': response_time,
            'confidence_score': confidence_score,
        })
        
        return cls.record_user_activity(
            user=user,
            activity_type='query',
            ip_address=ip_address,
            session_id=session_id,
            status='success' if success else 'failure',
            metadata=metadata
        )
    
    @classmethod
    def record_document_view(cls, user, document_id, document_type, ip_address=None, 
                            session_id=None, metadata=None):
        """
        Record a document view.
        
        Args:
            user: User object or None for anonymous users
            document_id: Document ID
            document_type: Document type (thesis, paper, protocol, etc.)
            ip_address: User's IP address (optional)
            session_id: Session ID (optional)
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        metadata.update({
            'document_type': document_type,
        })
        
        return cls.record_user_activity(
            user=user,
            activity_type='document_view',
            ip_address=ip_address,
            session_id=session_id,
            resource_id=document_id,
            resource_type=document_type,
            metadata=metadata
        )
    
    @classmethod
    def record_document_upload(cls, user, document_id, document_type, filename, 
                              filesize=None, ip_address=None, session_id=None, metadata=None):
        """
        Record a document upload.
        
        Args:
            user: User object or None for anonymous users
            document_id: Document ID
            document_type: Document type (thesis, paper, protocol, etc.)
            filename: Original filename
            filesize: File size in bytes (optional)
            ip_address: User's IP address (optional)
            session_id: Session ID (optional)
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        metadata.update({
            'document_type': document_type,
            'filename': filename,
            'filesize': filesize,
        })
        
        return cls.record_user_activity(
            user=user,
            activity_type='document_upload',
            ip_address=ip_address,
            session_id=session_id,
            resource_id=document_id,
            resource_type=document_type,
            metadata=metadata
        )
    
    @classmethod
    def record_feedback(cls, user, feedback_type, query_id, rating, comments=None, 
                       ip_address=None, session_id=None, metadata=None):
        """
        Record user feedback.
        
        Args:
            user: User object or None for anonymous users
            feedback_type: Type of feedback (thumbs_up, thumbs_down, rating, etc.)
            query_id: ID of the query being rated
            rating: Numerical rating or None
            comments: User comments (optional)
            ip_address: User's IP address (optional)
            session_id: Session ID (optional)
            metadata: Additional metadata (optional)
        """
        metadata = metadata or {}
        metadata.update({
            'feedback_type': feedback_type,
            'rating': rating,
            'comments': comments,
        })
        
        return cls.record_user_activity(
            user=user,
            activity_type='feedback',
            ip_address=ip_address,
            session_id=session_id,
            resource_id=query_id,
            resource_type='query',
            metadata=metadata
        )


class AuditCollector:
    """
    Collects and stores audit events for security and compliance.
    Provides methods for recording various types of audit events.
    """
    
    @classmethod
    def record_audit_event(cls, event_type, description, user=None, ip_address=None, 
                          severity="info", details=None):
        """
        Record an audit event.
        
        Args:
            event_type: Type of event (see AuditEvent.EVENT_TYPES)
            description: Description of the event
            user: User object or None for anonymous/system events
            ip_address: IP address related to the event (optional)
            severity: Event severity (info, warning, error, critical)
            details: Additional details as dictionary (optional)
        """
        details = details or {}
        
        try:
            # Don't store user object for anonymous users
            user_obj = None if isinstance(user, AnonymousUser) else user
            
            AuditEvent.objects.create(
                event_type=event_type,
                user=user_obj,
                timestamp=timezone.now(),
                ip_address=ip_address,
                description=description,
                severity=severity,
                details=details
            )
            return True
        except Exception as e:
            logger.error(f"Error recording audit event: {str(e)}")
            return False
    
    @classmethod
    def record_authentication_event(cls, success, user=None, username=None, 
                                   ip_address=None, details=None):
        """
        Record an authentication event.
        
        Args:
            success: Whether authentication was successful
            user: User object or None for failed authentications
            username: Username for failed authentications
            ip_address: IP address of the authentication attempt
            details: Additional details as dictionary (optional)
        """
        details = details or {}
        
        if username and not user:
            details['username'] = username
        
        description = "Successful authentication" if success else "Failed authentication attempt"
        severity = "info" if success else "warning"
        
        return cls.record_audit_event(
            event_type="authentication",
            description=description,
            user=user,
            ip_address=ip_address,
            severity=severity,
            details=details
        )
    
    @classmethod
    def record_authorization_event(cls, user, resource, action, success, 
                                  ip_address=None, details=None):
        """
        Record an authorization event.
        
        Args:
            user: User object or None for anonymous users
            resource: Resource being accessed
            action: Action being performed
            success: Whether authorization was successful
            ip_address: IP address of the authorization attempt
            details: Additional details as dictionary (optional)
        """
        details = details or {}
        details.update({
            'resource': resource,
            'action': action,
        })
        
        description = f"{'Authorized' if success else 'Unauthorized'} {action} on {resource}"
        severity = "info" if success else "warning"
        
        return cls.record_audit_event(
            event_type="authorization",
            description=description,
            user=user,
            ip_address=ip_address,
            severity=severity,
            details=details
        )
    
    @classmethod
    def record_data_access(cls, user, resource_type, resource_id, action, 
                          ip_address=None, details=None):
        """
        Record a data access event.
        
        Args:
            user: User object or None for anonymous users
            resource_type: Type of resource being accessed
            resource_id: ID of resource being accessed
            action: Action being performed (view, download, etc.)
            ip_address: IP address of the access attempt
            details: Additional details as dictionary (optional)
        """
        details = details or {}
        details.update({
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
        })
        
        description = f"{action.capitalize()} {resource_type} (ID: {resource_id})"
        
        return cls.record_audit_event(
            event_type="data_access",
            description=description,
            user=user,
            ip_address=ip_address,
            severity="info",
            details=details
        )
    
    @classmethod
    def record_pii_detection(cls, user, content_type, detection_method, 
                            ip_address=None, details=None, redacted=False):
        """
        Record a PII detection event.
        
        Args:
            user: User object or None for anonymous users
            content_type: Type of content where PII was detected
            detection_method: Method used to detect PII (regex, NER, etc.)
            ip_address: IP address related to the event
            details: Additional details as dictionary (optional)
            redacted: Whether the PII was automatically redacted
        """
        details = details or {}
        details.update({
            'content_type': content_type,
            'detection_method': detection_method,
            'redacted': redacted,
        })
        
        description = f"PII detected in {content_type} using {detection_method}"
        if redacted:
            description += " (automatically redacted)"
        
        return cls.record_audit_event(
            event_type="pii_detection",
            description=description,
            user=user,
            ip_address=ip_address,
            severity="warning",
            details=details
        )


class SecurityCollector:
    """
    Collects and stores security events.
    Provides methods for recording various types of security events.
    """
    
    @classmethod
    def record_security_event(cls, event_type, description, user=None, ip_address=None, 
                             severity="warning", details=None, is_resolved=False):
        """
        Record a security event.
        
        Args:
            event_type: Type of event (see SecurityEvent.EVENT_TYPES)
            description: Description of the event
            user: User object or None for anonymous/system events
            ip_address: IP address related to the event (optional)
            severity: Event severity (info, warning, error, critical)
            details: Additional details as dictionary (optional)
            is_resolved: Whether the event is already resolved
        """
        details = details or {}
        
        try:
            # Don't store user object for anonymous users
            user_obj = None if isinstance(user, AnonymousUser) else user
            
            SecurityEvent.objects.create(
                event_type=event_type,
                user=user_obj,
                timestamp=timezone.now(),
                ip_address=ip_address,
                description=description,
                severity=severity,
                details=details,
                is_resolved=is_resolved
            )
            return True
        except Exception as e:
            logger.error(f"Error recording security event: {str(e)}")
            return False
    
    @classmethod
    def record_login_failure(cls, username, ip_address=None, attempt_count=None, 
                            details=None):
        """
        Record a login failure security event.
        
        Args:
            username: Username that failed to authenticate
            ip_address: IP address of the login attempt
            attempt_count: Number of failed attempts (optional)
            details: Additional details as dictionary (optional)
        """
        details = details or {}
        details.update({
            'username': username,
            'attempt_count': attempt_count,
        })
        
        description = f"Failed login attempt for user '{username}'"
        if attempt_count and attempt_count > 3:
            description += f" ({attempt_count} attempts)"
            severity = "error" if attempt_count > 5 else "warning"
        else:
            severity = "warning"
        
        return cls.record_security_event(
            event_type="login_failure",
            description=description,
            ip_address=ip_address,
            severity=severity,
            details=details
        )
    
    @classmethod
    def record_access_denied(cls, user, resource, action, ip_address=None, 
                            details=None):
        """
        Record an access denied security event.
        
        Args:
            user: User object or None for anonymous users
            resource: Resource being accessed
            action: Action being performed
            ip_address: IP address of the access attempt
            details: Additional details as dictionary (optional)
        """
        details = details or {}
        details.update({
            'resource': resource,
            'action': action,
        })
        
        user_str = user.username if user and not isinstance(user, AnonymousUser) else "Anonymous user"
        description = f"Access denied: {user_str} attempted to {action} {resource}"
        
        return cls.record_security_event(
            event_type="access_denied",
            description=description,
            user=user,
            ip_address=ip_address,
            severity="warning",
            details=details
        )
    
    @classmethod
    def record_suspicious_activity(cls, activity_type, detection_method, user=None, 
                                  ip_address=None, details=None):
        """
        Record a suspicious activity security event.
        
        Args:
            activity_type: Type of suspicious activity
            detection_method: Method used to detect the activity
            user: User object or None for anonymous users
            ip_address: IP address related to the activity
            details: Additional details as dictionary (optional)
        """
        details = details or {}
        details.update({
            'activity_type': activity_type,
            'detection_method': detection_method,
        })
        
        user_str = user.username if user and not isinstance(user, AnonymousUser) else "Anonymous user"
        description = f"Suspicious activity detected: {activity_type} by {user_str}"
        
        return cls.record_security_event(
            event_type="suspicious_activity",
            description=description,
            user=user,
            ip_address=ip_address,
            severity="error",
            details=details
        )
    
    @classmethod
    def record_rate_limit_event(cls, event_level, path, user=None, ip_address=None, 
                               client_id=None, request_count=None, limit=None, details=None):
        """
        Record a rate limiting security event.
        
        Args:
            event_level: Level of rate limit event ('warning', 'exceeded', 'blocked')
            path: API path that was rate limited
            user: User object or None for anonymous users
            ip_address: IP address of the client
            client_id: Client identifier used for rate limiting
            request_count: Current request count
            limit: Rate limit that was applied
            details: Additional details as dictionary (optional)
        """
        details = details or {}
        details.update({
            'path': path,
            'client_id': client_id,
            'request_count': request_count,
            'limit': limit,
        })
        
        user_str = user.username if user and not isinstance(user, AnonymousUser) else "Anonymous user"
        
        if event_level == 'warning':
            description = f"Rate limit warning: {user_str} approaching limit for {path} ({request_count}/{limit.split('/')[0]})"
            event_type = "rate_limit_warning"
            severity = "info"
        elif event_level == 'exceeded':
            description = f"Rate limit exceeded: {user_str} exceeded limit for {path} ({request_count}/{limit.split('/')[0]})"
            event_type = "rate_limit_exceeded"
            severity = "warning"
        elif event_level == 'blocked':
            description = f"Rate limit enforced: {user_str} blocked from {path} due to excessive requests"
            event_type = "rate_limit_blocked"
            severity = "error"
        else:
            description = f"Rate limit event: {user_str} on {path}"
            event_type = "rate_limit_warning"
            severity = "info"
        
        return cls.record_security_event(
            event_type=event_type,
            description=description,
            user=user,
            ip_address=ip_address,
            severity=severity,
            details=details
        )