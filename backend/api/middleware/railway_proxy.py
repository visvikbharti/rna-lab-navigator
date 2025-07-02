"""
Railway proxy middleware to handle Railway edge server issues
"""
import logging

logger = logging.getLogger(__name__)


class RailwayProxyMiddleware:
    """
    Middleware to handle Railway's proxy headers and prevent redirect loops
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log incoming headers for debugging
        logger.info(f"Incoming request to {request.path}")
        logger.info(f"Headers: {dict(request.META)}")
        
        # Force HTTPS scheme if X-Forwarded-Proto is https
        if request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
            request._is_secure_override = True
        
        # Handle Railway-specific headers
        if 'HTTP_X_RAILWAY_REQUEST_ID' in request.META:
            request.railway_request_id = request.META['HTTP_X_RAILWAY_REQUEST_ID']
        
        # Get the response
        response = self.get_response(request)
        
        # Prevent Railway from adding its own redirects
        if response.status_code == 301:
            logger.warning(f"301 redirect from {request.path} to {response.get('Location', 'unknown')}")
            # If Railway is redirecting to the same URL, return 200 instead
            if response.get('Location') == request.build_absolute_uri():
                logger.warning("Detected Railway redirect loop, returning 200 instead")
                from django.http import HttpResponse
                return HttpResponse("OK", status=200)
        
        return response
    
    def process_request(self, request):
        """
        Override is_secure to respect Railway proxy headers
        """
        def _is_secure():
            # Trust Railway's X-Forwarded-Proto header
            if request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
                return True
            return request._is_secure_override if hasattr(request, '_is_secure_override') else False
        
        request.is_secure = _is_secure