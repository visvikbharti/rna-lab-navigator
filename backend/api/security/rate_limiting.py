"""
Rate limiting middleware for RNA Lab Navigator.
Implements OWASP API Security recommendation for rate limiting.
"""

import time
import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser

# Import the analytics security collector
from api.analytics.collectors import SecurityCollector

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class RateLimitingMiddleware:
    """
    Middleware that implements rate limiting for API endpoints.
    Uses Redis cache to track request counts per client.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'ENABLE_RATE_LIMITING', True)
        
        # Paths that should be rate limited (from settings)
        self.rate_limited_paths = [
            '/api/query/',
            '/api/search/',
            '/api/upload/',
            '/api/auth/',
            '/api/feedback/',
        ]
        
        # Paths to exclude from rate limiting
        self.excluded_paths = [
            '/api/health/',
            '/api/static/',
            '/api/media/',
            '/admin/',
        ]
        
        logger.info(f"Rate Limiting Middleware initialized - enabled: {self.enabled}")
    
    def __call__(self, request):
        # Skip middleware if disabled or for excluded paths
        if not self.enabled:
            return self.get_response(request)
        
        # Skip rate limiting for superusers
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)
            
        for excluded in self.excluded_paths:
            if request.path.startswith(excluded):
                return self.get_response(request)
        
        # Check if path should be rate limited
        should_limit = False
        
        for prefix in self.rate_limited_paths:
            if request.path.startswith(prefix):
                should_limit = True
                break
        
        if should_limit:
            try:
                # Get client identifier (IP address, API key, or user ID)
                client_id = self._get_client_identifier(request)
                
                # Check if client is exempt from rate limiting
                if self._is_client_exempt(client_id):
                    return self.get_response(request)
                
                # Check if client is blocked
                block_key = f"ratelimit:{client_id}:blocked"
                if cache.get(block_key):
                    # Log blocked request if analytics enabled
                    if getattr(settings, 'RATE_LIMIT_ANALYTICS', False):
                        user = request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None
                        ip = self._get_client_ip(request)
                        
                        SecurityCollector.record_rate_limit_event(
                            event_level='blocked',
                            path=request.path,
                            user=user,
                            ip_address=ip,
                            client_id=client_id,
                            details={'method': request.method}
                        )
                    
                    # Return blocked response
                    return self._build_rate_limit_response(
                        status=429,
                        message="Too many requests. You have been temporarily blocked due to excessive requests.",
                        retry_after=cache.ttl(block_key) or 300
                    )
                
                # Get rate limit for this path
                limit, window, period_name = self._get_rate_limit_for_path(request.path)
                
                # Check rate limit
                request_count = self._increment_request_count(client_id, request.path, window)
                
                # Check if rate limit exceeded
                if request_count > limit:
                    # Block client if configured to do so
                    block_duration = getattr(settings, 'RATE_LIMIT_BLOCK_DURATION', 0)
                    if block_duration > 0:
                        self._block_client(client_id, block_duration)
                    
                    # Log exceeded rate limit if analytics enabled
                    if getattr(settings, 'RATE_LIMIT_ANALYTICS', False):
                        user = request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None
                        ip = self._get_client_ip(request)
                        
                        SecurityCollector.record_rate_limit_event(
                            event_level='exceeded',
                            path=request.path,
                            user=user,
                            ip_address=ip,
                            client_id=client_id,
                            request_count=request_count,
                            limit=f"{limit}/{period_name}",
                            details={'method': request.method}
                        )
                    
                    # Return rate limit exceeded response
                    return self._build_rate_limit_response(
                        status=429,
                        message=f"Rate limit exceeded. Please try again later.",
                        request_count=request_count,
                        limit=limit,
                        period=period_name,
                        retry_after=window
                    )
                
                # Log warning for approaching rate limit (80% of limit)
                if request_count > (limit * 0.8):
                    if getattr(settings, 'RATE_LIMIT_ANALYTICS', False):
                        user = request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None
                        ip = self._get_client_ip(request)
                        
                        SecurityCollector.record_rate_limit_event(
                            event_level='warning',
                            path=request.path,
                            user=user,
                            ip_address=ip,
                            client_id=client_id,
                            request_count=request_count,
                            limit=f"{limit}/{period_name}",
                            details={'method': request.method}
                        )
                
                # Continue with request
                response = self.get_response(request)
                
                # Add rate limit headers to response
                self._add_rate_limit_headers(response, request_count, limit, window)
                
                return response
            except Exception as e:
                logger.error(f"Error in rate limiting middleware: {str(e)}")
                # Continue with request in case of error
                return self.get_response(request)
        else:
            # Not a rate limited path
            return self.get_response(request)
    
    def _get_client_identifier(self, request: HttpRequest) -> str:
        """
        Get a unique identifier for the client making the request.
        Uses API key, user ID, or IP address in that order of preference.
        
        Args:
            request: The HTTP request
            
        Returns:
            String identifier for the client
        """
        # First try API key (if using token authentication)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer ') or auth_header.startswith('Token '):
            token = auth_header.split(' ')[1]
            return f"token:{token}"
        
        # Next try authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Finally use IP address
        ip = self._get_client_ip(request)
        return f"ip:{ip}"
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Get client IP address from request, handling proxy headers.
        
        Args:
            request: The HTTP request
            
        Returns:
            Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get first IP in case of multiple proxies
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def _is_client_exempt(self, client_id: str) -> bool:
        """
        Check if a client is exempt from rate limiting.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Boolean indicating if client is exempt
        """
        exemptions = getattr(settings, 'RATE_LIMIT_EXEMPTIONS', [])
        
        # Check IP exemptions
        if client_id.startswith('ip:'):
            ip = client_id[3:]
            if ip in exemptions:
                return True
        
        # Check user exemptions
        if client_id.startswith('user:'):
            user_id = client_id[5:]
            if user_id in exemptions or f"user:{user_id}" in exemptions:
                return True
        
        return False
    
    def _get_rate_limit_for_path(self, path: str) -> Tuple[int, int, str]:
        """
        Get the rate limit for a path from settings.
        
        Args:
            path: The request path
            
        Returns:
            Tuple of (limit, period_seconds, period_name)
        """
        # Default rate limit
        default_rate_limit = getattr(settings, 'RATE_LIMIT_DEFAULT', '60/minute')
        
        # Get rate limit rules from settings
        rate_limit_rules = getattr(settings, 'RATE_LIMIT_RULES', {})
        
        # Find the most specific matching rule
        matching_rule = None
        max_match_length = 0
        
        for rule_path, limit in rate_limit_rules.items():
            # Exact match
            if path == rule_path:
                return self._parse_rate_limit(limit)
            
            # Prefix match (most specific one wins)
            if path.startswith(rule_path) and len(rule_path) > max_match_length:
                matching_rule = limit
                max_match_length = len(rule_path)
        
        # Use matching rule or default
        rate_limit = matching_rule or default_rate_limit
        return self._parse_rate_limit(rate_limit)
    
    def _parse_rate_limit(self, rate_limit: str) -> Tuple[int, int, str]:
        """
        Parse a rate limit string in format 'number/period'.
        
        Args:
            rate_limit: Rate limit string like '60/minute'
            
        Returns:
            Tuple of (limit, period_seconds, period_name)
        """
        if not rate_limit or '/' not in rate_limit:
            return 60, 60, 'minute'  # Default: 60 per minute
        
        try:
            limit, period = rate_limit.split('/')
            limit = int(limit)
            
            # Convert period to seconds
            if period.lower() in ['s', 'sec', 'second', 'seconds']:
                period_seconds = 1
                period_name = 'second'
            elif period.lower() in ['m', 'min', 'minute', 'minutes']:
                period_seconds = 60
                period_name = 'minute'
            elif period.lower() in ['h', 'hour', 'hours']:
                period_seconds = 3600
                period_name = 'hour'
            elif period.lower() in ['d', 'day', 'days']:
                period_seconds = 86400
                period_name = 'day'
            else:
                period_seconds = 60
                period_name = 'minute'
            
            return limit, period_seconds, period_name
        except Exception as e:
            logger.error(f"Error parsing rate limit '{rate_limit}': {str(e)}")
            return 60, 60, 'minute'  # Default: 60 per minute
    
    def _increment_request_count(self, client_id: str, path: str, period_seconds: int) -> int:
        """
        Increment the request count for a client and path.
        
        Args:
            client_id: Client identifier
            path: Request path
            period_seconds: Rate limit period in seconds
            
        Returns:
            Current request count in the period
        """
        # Create a normalized path key (remove numeric IDs from path for grouping similar endpoints)
        norm_path = re.sub(r'/\d+/', '/:id/', path)
        norm_path = re.sub(r'/\d+$', '/:id', norm_path)
        
        # Create cache keys
        count_key = f"ratelimit:{client_id}:{norm_path}:count"
        expires_key = f"ratelimit:{client_id}:{norm_path}:expires"
        
        # Get current count and expiration time
        count = cache.get(count_key, 0)
        expires = cache.get(expires_key)
        
        current_time = int(time.time())
        
        if not expires or current_time > expires:
            # First request in a new period
            expires = current_time + period_seconds
            count = 1
            
            # Set cache with expiration
            cache.set(count_key, count, period_seconds)
            cache.set(expires_key, expires, period_seconds)
        else:
            # Increment the count
            count += 1
            cache.set(count_key, count, cache.ttl(count_key))
        
        return count
    
    def _block_client(self, client_id: str, duration: int = None) -> None:
        """
        Block a client for a specified duration.
        
        Args:
            client_id: Client identifier
            duration: Duration in seconds (default: from settings)
        """
        if duration is None:
            duration = getattr(settings, 'RATE_LIMIT_BLOCK_DURATION', 300)
        
        block_key = f"ratelimit:{client_id}:blocked"
        cache.set(block_key, True, duration)
        
        logger.warning(f"Client {client_id} blocked for {duration} seconds due to rate limit violation")
    
    def _build_rate_limit_response(self, status: int, message: str, 
                                  request_count: int = None, limit: int = None, 
                                  period: str = None, retry_after: int = None) -> JsonResponse:
        """
        Build a rate limit error response.
        
        Args:
            status: HTTP status code
            message: Error message
            request_count: Current request count
            limit: Rate limit
            period: Rate limit period name
            retry_after: Seconds to wait before retrying
            
        Returns:
            JsonResponse with appropriate status and headers
        """
        data = {
            'error': 'Rate limit exceeded',
            'message': message,
            'status': status,
        }
        
        if request_count is not None and limit is not None:
            data.update({
                'request_count': request_count,
                'limit': limit,
            })
            
            if period:
                data['period'] = period
        
        response = JsonResponse(data, status=status)
        
        # Add Retry-After header if provided
        if retry_after:
            response['Retry-After'] = retry_after
        
        # Add rate limit headers
        if request_count is not None and limit is not None:
            self._add_rate_limit_headers(response, request_count, limit, retry_after or 60)
        
        return response
    
    def _add_rate_limit_headers(self, response: HttpResponse, request_count: int, 
                              limit: int, window: int) -> None:
        """
        Add rate limit headers to response.
        
        Args:
            response: The HTTP response
            request_count: Current request count
            limit: Rate limit
            window: Time window in seconds
        """
        # Standard rate limit headers
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(max(0, limit - request_count))
        response['X-RateLimit-Reset'] = str(int(time.time() + window))
        
        # RFC-compliant RateLimit headers (RFC 6585)
        response['RateLimit-Limit'] = str(limit)
        response['RateLimit-Remaining'] = str(max(0, limit - request_count))
        response['RateLimit-Reset'] = str(int(time.time() + window))
        
        if request_count >= limit:
            response['Retry-After'] = str(window)


# Helper functions for rate limiting in views
def check_rate_limit(client_id: str, action: str, limit: int = None, window: int = None) -> bool:
    """
    Check rate limit for a specific action.
    Can be used directly in views for specialized rate limiting.
    
    Args:
        client_id: Client identifier
        action: Action name (e.g., 'model_upload', 'bulk_delete')
        limit: Number of allowed requests per window (default: from settings)
        window: Time window in seconds (default: from settings)
        
    Returns:
        True if limit is not exceeded, False otherwise
    """
    # Use settings if limit or window not specified
    if limit is None:
        default_rate_limit = getattr(settings, 'RATE_LIMIT_DEFAULT', '60/minute')
        parts = default_rate_limit.split('/')
        limit = int(parts[0]) if len(parts) > 0 else 60
    
    if window is None:
        default_rate_limit = getattr(settings, 'RATE_LIMIT_DEFAULT', '60/minute')
        parts = default_rate_limit.split('/')
        period = parts[1] if len(parts) > 1 else 'minute'
        
        # Convert period to seconds
        if period.lower() in ['s', 'sec', 'second', 'seconds']:
            window = 1
        elif period.lower() in ['m', 'min', 'minute', 'minutes']:
            window = 60
        elif period.lower() in ['h', 'hour', 'hours']:
            window = 3600
        elif period.lower() in ['d', 'day', 'days']:
            window = 86400
        else:
            window = 60
    
    cache_key = f"ratelimit:{client_id}:{action}:count"
    count = cache.get(cache_key, 0)
    
    if count == 0:
        # First request, set initial count
        cache.set(cache_key, 1, window)
        return True
    
    # Check if limit exceeded
    if count >= limit:
        return False
    
    # Increment count
    cache.incr(cache_key)
    return True


def track_rate_limit(request: HttpRequest, action: str, limit: int = None, window: int = None) -> bool:
    """
    Track and check rate limit for a specific action using the current request.
    Automatically extracts client identifier from request.
    
    Args:
        request: HTTP request object
        action: Action name (e.g., 'model_upload', 'bulk_delete')
        limit: Number of allowed requests per window (default: from settings)
        window: Time window in seconds (default: from settings)
        
    Returns:
        True if limit is not exceeded, False otherwise
    """
    # Extract client identifier from request
    client_id = None
    
    # First try API key (if using token authentication)
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer ') or auth_header.startswith('Token '):
        token = auth_header.split(' ')[1]
        client_id = f"token:{token}"
    
    # Next try authenticated user
    elif hasattr(request, 'user') and request.user.is_authenticated:
        client_id = f"user:{request.user.id}"
    
    # Finally use IP address
    else:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        client_id = f"ip:{ip}"
    
    # Skip rate limiting for superusers
    if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
        return True
    
    # Check exemptions
    exemptions = getattr(settings, 'RATE_LIMIT_EXEMPTIONS', [])
    if client_id.startswith('ip:') and client_id[3:] in exemptions:
        return True
    if client_id.startswith('user:') and (client_id[5:] in exemptions or client_id in exemptions):
        return True
    
    # Check rate limit
    return check_rate_limit(client_id, action, limit, window)


def block_client(client_id: str, duration: int = None) -> None:
    """
    Block a client for a specified duration.
    
    Args:
        client_id: Client identifier
        duration: Duration in seconds (default: from settings)
    """
    if duration is None:
        duration = getattr(settings, 'RATE_LIMIT_BLOCK_DURATION', 300)
    
    block_key = f"ratelimit:{client_id}:blocked"
    cache.set(block_key, True, duration)
    
    logger.warning(f"Client {client_id} blocked for {duration} seconds")