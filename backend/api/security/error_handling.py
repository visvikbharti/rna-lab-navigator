"""
Error handling utilities for security features in RNA Lab Navigator.
Provides standardized error handling, logging, and recovery for security components.
"""

import logging
import traceback
import functools
import json
from typing import Dict, Any, Optional, Callable, Type, Union
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

# Define security error types
class SecurityError(Exception):
    """Base class for security-related errors"""
    status_code = 500
    error_code = "security_error"
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(SecurityError):
    """Error related to authentication"""
    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(SecurityError):
    """Error related to authorization"""
    status_code = 403
    error_code = "authorization_error"


class PIIDetectionError(SecurityError):
    """Error related to PII detection"""
    status_code = 500
    error_code = "pii_detection_error"


class DifferentialPrivacyError(SecurityError):
    """Error related to differential privacy"""
    status_code = 500
    error_code = "differential_privacy_error"


class SecurityConfigurationError(SecurityError):
    """Error related to security configuration"""
    status_code = 500
    error_code = "security_configuration_error"


class ConnectionSecurityError(SecurityError):
    """Error related to connection security"""
    status_code = 500
    error_code = "connection_security_error"


class SecurityHeaders:
    """Constants for security headers"""
    CONTENT_SECURITY_POLICY = "Content-Security-Policy"
    X_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
    X_FRAME_OPTIONS = "X-Frame-Options"
    X_XSS_PROTECTION = "X-XSS-Protection"
    REFERRER_POLICY = "Referrer-Policy"
    STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"
    PERMISSIONS_POLICY = "Permissions-Policy"


def handle_security_error(
    error: SecurityError, 
    request: Optional[HttpRequest] = None
) -> Dict[str, Any]:
    """
    Handle a security error with appropriate logging and response.
    
    Args:
        error: The security error
        request: Optional HTTP request
        
    Returns:
        Dict with error response data
    """
    # Log detailed error information
    log_message = f"Security error: {error.error_code} - {error.message}"
    
    # Add request info if available
    if request:
        log_message += f" - Path: {request.path}"
        if hasattr(request, "user") and request.user:
            log_message += f" - User: {request.user.username}"
            
    # Log error details
    if error.details:
        log_message += f" - Details: {json.dumps(error.details)}"
        
    # Log traceback for server errors
    if error.status_code >= 500:
        logger.error(log_message, exc_info=True)
    else:
        logger.warning(log_message)
        
    # Prepare error response
    response_data = {
        "error": error.error_code,
        "message": error.message,
    }
    
    # Add details for non-production environments
    if settings.DEBUG:
        response_data["details"] = error.details
        response_data["traceback"] = traceback.format_exc()
        
    return response_data


def security_error_to_response(
    error: SecurityError, 
    request: Optional[HttpRequest] = None
) -> JsonResponse:
    """
    Convert a security error to an HTTP response.
    
    Args:
        error: The security error
        request: Optional HTTP request
        
    Returns:
        JsonResponse with appropriate status code
    """
    response_data = handle_security_error(error, request)
    return JsonResponse(response_data, status=error.status_code)


def security_exception_handler(
    exception_classes: Union[Type[Exception], tuple],
    status_code: int = 500,
    error_code: str = "security_error"
):
    """
    Decorator to handle exceptions in security-related views.
    
    Args:
        exception_classes: Exception class or tuple of classes to catch
        status_code: HTTP status code for the response
        error_code: Error code for the response
        
    Returns:
        Decorator function
    """
    def decorator(view_func: Callable):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except exception_classes as e:
                # Convert to SecurityError if it's not already
                if not isinstance(e, SecurityError):
                    error = SecurityError(str(e))
                    error.status_code = status_code
                    error.error_code = error_code
                else:
                    error = e
                    
                return security_error_to_response(error, request)
                
        return wrapper
    return decorator


class SecurityMiddleware:
    """Middleware to handle security-related errors"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        try:
            response = self.get_response(request)
            
            # Ensure security headers are present
            if hasattr(response, "headers"):
                self._ensure_security_headers(response)
                
            return response
            
        except SecurityError as e:
            return security_error_to_response(e, request)
            
        except Exception as e:
            # Don't catch all exceptions in production
            if not settings.DEBUG:
                raise
                
            # In debug mode, convert to security error
            error = SecurityError(f"Unhandled security error: {str(e)}")
            return security_error_to_response(error, request)
    
    def _ensure_security_headers(self, response):
        """Ensure critical security headers are present"""
        # Backup headers - these should be set by SecurityHeadersMiddleware,
        # but this provides a failsafe
        if SecurityHeaders.X_CONTENT_TYPE_OPTIONS not in response.headers:
            response.headers[SecurityHeaders.X_CONTENT_TYPE_OPTIONS] = "nosniff"
            
        if SecurityHeaders.X_FRAME_OPTIONS not in response.headers:
            response.headers[SecurityHeaders.X_FRAME_OPTIONS] = "DENY"


# Convenience functions

def log_security_event(
    event_type: str,
    message: str,
    severity: str = "info",
    details: Optional[Dict[str, Any]] = None,
    user = None
):
    """
    Log a security event with standardized format.
    
    Args:
        event_type: Type of security event
        message: Event message
        severity: Log severity (info, warning, error)
        details: Additional details
        user: User associated with the event
    """
    log_data = {
        "event_type": event_type,
        "message": message,
        "details": details or {},
    }
    
    if user:
        if hasattr(user, "username"):
            log_data["username"] = user.username
        if hasattr(user, "id"):
            log_data["user_id"] = user.id
            
    log_json = json.dumps(log_data)
    
    if severity == "error":
        logger.error(f"SECURITY_EVENT: {log_json}")
    elif severity == "warning":
        logger.warning(f"SECURITY_EVENT: {log_json}")
    else:
        logger.info(f"SECURITY_EVENT: {log_json}")


def add_secure_headers(response: HttpResponse) -> HttpResponse:
    """
    Add security headers to a response.
    
    Args:
        response: HTTP response
        
    Returns:
        HTTP response with security headers
    """
    response.headers[SecurityHeaders.X_CONTENT_TYPE_OPTIONS] = "nosniff"
    response.headers[SecurityHeaders.X_FRAME_OPTIONS] = "DENY"
    response.headers[SecurityHeaders.X_XSS_PROTECTION] = "1; mode=block"
    response.headers[SecurityHeaders.REFERRER_POLICY] = "strict-origin-when-cross-origin"
    
    # Add HSTS in production
    if not settings.DEBUG:
        response.headers[SecurityHeaders.STRICT_TRANSPORT_SECURITY] = "max-age=31536000; includeSubDomains"
        
    return response


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that handles security exceptions.
    
    Args:
        exc: The raised exception
        context: The context for the exception
        
    Returns:
        Response object with appropriate error details or None
    """
    from rest_framework.views import exception_handler
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If standard handler returns a response, return it
    if response is not None:
        return response
    
    # Handle SecurityError explicitly
    if isinstance(exc, SecurityError):
        return security_error_to_response(exc, context.get('request'))
    
    # For other exceptions in debug mode, provide more details
    if settings.DEBUG:
        if isinstance(exc, Exception):
            error = SecurityError(f"Unhandled error: {str(exc)}")
            error.details = {
                "error_type": exc.__class__.__name__,
                "exception": str(exc),
            }
            return security_error_to_response(error, context.get('request'))
    
    # Otherwise return None and let Django's standard handler deal with it
    return None