"""
Performance monitoring middleware for Django.

This middleware automatically tracks performance metrics for all requests,
providing real-time insights into system performance and bottlenecks.
"""

import time
import logging
from typing import Dict, Any
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.db import connection
from .performance_profiler import get_profiler

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor performance of Django requests.
    
    Tracks:
    - Request/response times
    - Database query counts and times
    - Memory usage changes
    - View-specific performance metrics
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.profiler = get_profiler()
        super().__init__(get_response)
    
    def process_request(self, request):
        """Called before view processing."""
        # Store request start time
        request._perf_start_time = time.time()
        request._perf_queries_start = len(connection.queries)
        
        # Get initial memory usage
        import psutil
        process = psutil.Process()
        request._perf_memory_start = process.memory_info().rss / (1024 * 1024)
    
    def process_response(self, request, response):
        """Called after view processing."""
        if not hasattr(request, '_perf_start_time'):
            return response
        
        # Calculate metrics
        end_time = time.time()
        total_time = end_time - request._perf_start_time
        
        # Database metrics
        queries_count = len(connection.queries) - request._perf_queries_start
        db_time = sum(float(query['time']) for query in connection.queries[request._perf_queries_start:])
        
        # Memory metrics
        import psutil
        process = psutil.Process()
        memory_end = process.memory_info().rss / (1024 * 1024)
        memory_delta = memory_end - request._perf_memory_start
        
        # Request metadata
        view_name = self._get_view_name(request)
        metadata = {
            'path': request.path,
            'method': request.method,
            'view_name': view_name,
            'status_code': response.status_code,
            'queries_count': queries_count,
            'db_time': db_time,
            'memory_delta_mb': memory_delta,
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        }
        
        # Record performance metric
        component = f"django.{request.method.lower()}"
        operation = view_name or request.path
        
        self.profiler.record_metric(component, operation, total_time, metadata)
        
        # Add performance headers for debugging
        if getattr(settings, 'PERFORMANCE_DEBUG_HEADERS', False):
            response['X-Response-Time'] = f"{total_time:.3f}s"
            response['X-DB-Queries'] = str(queries_count)
            response['X-DB-Time'] = f"{db_time:.3f}s"
            response['X-Memory-Delta'] = f"{memory_delta:.2f}MB"
        
        # Log slow requests
        slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 5.0)
        if total_time > slow_threshold:
            logger.warning(f"Slow request detected: {request.method} {request.path} "
                         f"took {total_time:.3f}s (threshold: {slow_threshold}s)")
        
        return response
    
    def _get_view_name(self, request) -> str:
        """Extract view name from request."""
        try:
            if hasattr(request, 'resolver_match') and request.resolver_match:
                if hasattr(request.resolver_match, 'view_name'):
                    return request.resolver_match.view_name
                elif hasattr(request.resolver_match, 'func'):
                    if hasattr(request.resolver_match.func, '__name__'):
                        return request.resolver_match.func.__name__
                    elif hasattr(request.resolver_match.func, 'view_class'):
                        return request.resolver_match.func.view_class.__name__
        except Exception:
            pass
        
        return 'unknown'


class RAGPerformanceMiddleware(MiddlewareMixin):
    """
    Specialized middleware for monitoring RAG pipeline performance.
    
    Specifically tracks query endpoints and provides detailed metrics
    for RAG operations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.profiler = get_profiler()
        super().__init__(get_response)
    
    def process_request(self, request):
        """Initialize RAG-specific tracking."""
        if self._is_rag_endpoint(request):
            request._rag_start_time = time.time()
            request._rag_tracking = True
    
    def process_response(self, request, response):
        """Track RAG-specific metrics."""
        if not getattr(request, '_rag_tracking', False):
            return response
        
        total_time = time.time() - request._rag_start_time
        
        # Extract query details from request/response
        query_details = self._extract_query_details(request, response)
        
        # Determine if this meets KPI requirements
        kpi_compliant = total_time <= 5.0
        
        metadata = {
            'kpi_compliant': kpi_compliant,
            'kpi_violation': not kpi_compliant,
            **query_details
        }
        
        # Record RAG-specific metric
        self.profiler.record_metric('rag_pipeline', 'query', total_time, metadata)
        
        # Log KPI violations
        if not kpi_compliant:
            logger.warning(f"KPI violation: RAG query took {total_time:.3f}s "
                         f"(exceeds 5.0s requirement)")
        
        return response
    
    def _is_rag_endpoint(self, request) -> bool:
        """Check if request is to a RAG endpoint."""
        rag_paths = ['/api/query/', '/api/search/', '/api/chat/']
        return any(request.path.startswith(path) for path in rag_paths)
    
    def _extract_query_details(self, request, response) -> Dict[str, Any]:
        """Extract query details from request/response."""
        details = {}
        
        try:
            # Extract from request body
            if hasattr(request, 'body') and request.body:
                import json
                body = json.loads(request.body.decode('utf-8'))
                details['query_text'] = body.get('question', '')
                details['doc_type'] = body.get('doc_type', '')
                details['query_length'] = len(details['query_text'])
                details['query_words'] = len(details['query_text'].split()) if details['query_text'] else 0
            
            # Extract from response
            if response.status_code == 200 and hasattr(response, 'content'):
                try:
                    import json
                    response_data = json.loads(response.content.decode('utf-8'))
                    details['confidence_score'] = response_data.get('confidence_score', 0)
                    details['sources_count'] = len(response_data.get('sources', []))
                    details['answer_length'] = len(response_data.get('answer', ''))
                except:
                    pass
            
        except Exception as e:
            logger.debug(f"Could not extract query details: {str(e)}")
        
        return details


class DatabaseQueryProfilerMiddleware(MiddlewareMixin):
    """
    Middleware for profiling database query performance.
    
    Tracks slow queries and provides insights into database bottlenecks.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.profiler = get_profiler()
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD', 0.1)  # 100ms
        super().__init__(get_response)
    
    def process_request(self, request):
        """Initialize database tracking."""
        request._db_queries_start = len(connection.queries)
    
    def process_response(self, request, response):
        """Analyze database queries."""
        if not hasattr(request, '_db_queries_start'):
            return response
        
        queries = connection.queries[request._db_queries_start:]
        
        for query in queries:
            query_time = float(query['time'])
            
            # Record slow queries
            if query_time > self.slow_query_threshold:
                metadata = {
                    'sql': query['sql'][:500],  # Truncate long queries
                    'query_time': query_time,
                    'request_path': request.path,
                    'is_slow': True
                }
                
                self.profiler.record_metric('database', 'slow_query', query_time, metadata)
                
                logger.warning(f"Slow database query: {query_time:.3f}s - {query['sql'][:100]}...")
        
        # Record overall database metrics for this request
        if queries:
            total_db_time = sum(float(q['time']) for q in queries)
            metadata = {
                'queries_count': len(queries),
                'total_db_time': total_db_time,
                'avg_query_time': total_db_time / len(queries),
                'request_path': request.path
            }
            
            self.profiler.record_metric('database', 'request_queries', total_db_time, metadata)
        
        return response


class CachePerformanceMiddleware(MiddlewareMixin):
    """
    Middleware for monitoring cache performance.
    
    Tracks cache hit/miss ratios and cache operation times.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.profiler = get_profiler()
        super().__init__(get_response)
        
        # Patch cache methods to track performance
        self._patch_cache_methods()
    
    def _patch_cache_methods(self):
        """Patch Django cache methods to track performance."""
        try:
            from django.core.cache import cache
            
            # Store original methods
            original_get = cache.get
            original_set = cache.set
            original_delete = cache.delete
            
            def patched_get(key, default=None, version=None):
                start_time = time.time()
                result = original_get(key, default, version)
                duration = time.time() - start_time
                
                hit = result is not None and result != default
                self.profiler.record_metric('cache', 'get', duration, {
                    'hit': hit,
                    'key': str(key)[:50]  # Truncate long keys
                })
                
                return result
            
            def patched_set(key, value, timeout=None, version=None):
                start_time = time.time()
                result = original_set(key, value, timeout, version)
                duration = time.time() - start_time
                
                self.profiler.record_metric('cache', 'set', duration, {
                    'key': str(key)[:50],
                    'timeout': timeout
                })
                
                return result
            
            def patched_delete(key, version=None):
                start_time = time.time()
                result = original_delete(key, version)
                duration = time.time() - start_time
                
                self.profiler.record_metric('cache', 'delete', duration, {
                    'key': str(key)[:50]
                })
                
                return result
            
            # Apply patches
            cache.get = patched_get
            cache.set = patched_set
            cache.delete = patched_delete
            
        except Exception as e:
            logger.error(f"Failed to patch cache methods: {str(e)}")
    
    def process_response(self, request, response):
        """No additional processing needed - metrics recorded in patched methods."""
        return response


# Utility function to enable performance monitoring
def enable_performance_monitoring():
    """
    Enable performance monitoring by adding middlewares to Django settings.
    
    Call this in your Django app's __init__.py or settings.py
    """
    from django.conf import settings
    
    performance_middlewares = [
        'tests.performance_monitoring.middleware.PerformanceMonitoringMiddleware',
        'tests.performance_monitoring.middleware.RAGPerformanceMiddleware',
        'tests.performance_monitoring.middleware.DatabaseQueryProfilerMiddleware',
        'tests.performance_monitoring.middleware.CachePerformanceMiddleware',
    ]
    
    if hasattr(settings, 'MIDDLEWARE'):
        for middleware in performance_middlewares:
            if middleware not in settings.MIDDLEWARE:
                settings.MIDDLEWARE.append(middleware)
    
    # Enable debug headers in development
    if settings.DEBUG:
        settings.PERFORMANCE_DEBUG_HEADERS = True
    
    logger.info("Performance monitoring enabled")