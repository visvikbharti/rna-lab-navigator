"""
Middleware for collecting analytics data from requests and responses.
Tracks response times, user activity, and provides data for the analytics dashboard.
"""

import time
import json
import uuid
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from .models import UserActivityLog, SystemMetric, AuditEvent


class AnalyticsMiddleware(MiddlewareMixin):
    """
    Middleware to collect analytics data from requests and responses.
    Tracks response times, request patterns, and user activity.
    """
    
    def process_request(self, request):
        # Add start time to request
        request.analytics_start_time = time.time()
        
        # Generate or retrieve request ID for tracking
        if not hasattr(request, 'request_id'):
            request.request_id = str(uuid.uuid4())
        
        return None
    
    def process_response(self, request, response):
        if not hasattr(request, 'analytics_start_time'):
            return response
        
        # Calculate response time
        response_time = (time.time() - request.analytics_start_time) * 1000  # in ms
        
        # Skip analytics for certain paths if needed
        if self._should_skip_analytics(request.path):
            return response
        
        # Record metrics
        try:
            self._record_metrics(request, response, response_time)
            self._record_user_activity(request, response, response_time)
        except Exception as e:
            # Log error but don't affect user response
            if settings.DEBUG:
                print(f"Analytics error: {str(e)}")
        
        return response
    
    def _should_skip_analytics(self, path):
        """Determine if analytics should be skipped for this path"""
        skip_prefixes = [
            '/static/',
            '/favicon.ico',
            '/admin/jsi18n/',
            '/__debug__/',  # Django Debug Toolbar
        ]
        return any(path.startswith(prefix) for prefix in skip_prefixes)
    
    def _record_metrics(self, request, response, response_time):
        """Record system metrics for this request/response"""
        # Record response time metric
        SystemMetric.objects.create(
            metric_type='response_time',
            value=response_time,
            unit='ms',
            metadata={
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'user_id': getattr(request.user, 'id', None),
            }
        )
    
    def _record_user_activity(self, request, response, response_time):
        """Record user activity for this request"""
        # Skip if it's a static file or similar
        if hasattr(request, 'user') and not self._should_skip_analytics(request.path):
            # Determine the activity type based on the path and method
            activity_type = self._determine_activity_type(request)
            
            # Get session ID if available
            session_id = request.session.session_key if hasattr(request, 'session') else None
            
            # Extract resource information
            resource_type, resource_id = self._extract_resource_info(request)
            
            # Determine if this was an API call and extract query if possible
            metadata = self._extract_metadata(request, response)
            
            # Create the activity log
            UserActivityLog.objects.create(
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                activity_type=activity_type,
                ip_address=self._get_client_ip(request),
                session_id=session_id,
                resource_id=resource_id,
                resource_type=resource_type,
                status='success' if 200 <= response.status_code < 400 else 'failure',
                metadata=metadata
            )
            
            # Record security-relevant events to the audit log if needed
            if self._is_security_relevant(request, response):
                self._record_audit_event(request, response)
    
    def _determine_activity_type(self, request):
        """Determine the type of activity from the request"""
        path = request.path.lower()
        method = request.method
        
        # Authentication activities
        if 'login' in path:
            return 'login'
        elif 'logout' in path:
            return 'logout'
        
        # Content interaction
        if method == 'GET':
            if 'document' in path or 'pdf' in path or 'thesis' in path:
                return 'document_view'
            elif 'api' in path:
                return 'query'
            elif 'admin' in path:
                return 'admin_action'
        elif method == 'POST':
            if 'upload' in path:
                return 'document_upload'
            elif 'feedback' in path:
                return 'feedback'
            elif 'settings' in path or 'config' in path:
                return 'setting_change'
            elif 'admin' in path:
                return 'admin_action'
            elif 'api' in path:
                return 'query'
        
        # Default
        return 'query'
    
    def _extract_resource_info(self, request):
        """Extract resource type and ID from the request path"""
        path_parts = request.path.strip('/').split('/')
        
        # Default values
        resource_type = None
        resource_id = None
        
        # Extract based on common API patterns
        if len(path_parts) >= 2:
            if path_parts[0] in ['api', 'v1', 'v2']:
                resource_type = path_parts[1]
                if len(path_parts) >= 3 and path_parts[2].isdigit():
                    resource_id = path_parts[2]
        
        return resource_type, resource_id
    
    def _extract_metadata(self, request, response):
        """Extract useful metadata from the request/response"""
        metadata = {
            'path': request.path,
            'method': request.method,
            'status_code': response.status_code,
        }
        
        # Attempt to extract query text from request body for chat/query endpoints
        if request.method == 'POST' and hasattr(request, 'body'):
            try:
                if request.content_type == 'application/json':
                    body = json.loads(request.body.decode('utf-8'))
                    if 'query' in body:
                        metadata['query_text'] = body['query']
                    elif 'question' in body:
                        metadata['query_text'] = body['question']
                    elif 'message' in body:
                        metadata['query_text'] = body['message']
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        
        # Add user agent info
        if 'HTTP_USER_AGENT' in request.META:
            metadata['user_agent'] = request.META['HTTP_USER_AGENT']
        
        return metadata
    
    def _get_client_ip(self, request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_security_relevant(self, request, response):
        """Determine if this request/response is security relevant for audit logging"""
        # Authentication events
        if 'login' in request.path.lower() or 'logout' in request.path.lower():
            return True
        
        # Admin actions
        if '/admin/' in request.path and request.method != 'GET':
            return True
        
        # Access errors
        if response.status_code in [401, 403, 404]:
            return True
        
        # Server errors
        if response.status_code >= 500:
            return True
        
        # Data modification
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            sensitive_paths = ['settings', 'users', 'admin', 'auth', 'permissions']
            if any(path in request.path.lower() for path in sensitive_paths):
                return True
        
        return False
    
    def _record_audit_event(self, request, response):
        """Record a security-relevant event to the audit log"""
        event_mapping = {
            'login': 'authentication',
            'logout': 'authentication',
            '/admin/': 'system_operation' if request.method == 'GET' else 'data_modification',
        }
        
        # Default to data_access for GETs and data_modification for other methods
        if request.method == 'GET':
            event_type = 'data_access'
        else:
            event_type = 'data_modification'
        
        # Check for specific path mappings
        for path_part, mapped_type in event_mapping.items():
            if path_part in request.path.lower():
                event_type = mapped_type
                break
        
        # Determine severity based on status code
        if response.status_code >= 500:
            severity = 'error'
        elif response.status_code in [401, 403]:
            severity = 'warning'
        else:
            severity = 'info'
        
        # Create the audit event
        AuditEvent.objects.create(
            event_type=event_type,
            user=request.user if not isinstance(request.user, AnonymousUser) else None,
            ip_address=self._get_client_ip(request),
            description=f"{request.method} {request.path} - {response.status_code}",
            severity=severity,
            details={
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', ''),
            }
        )