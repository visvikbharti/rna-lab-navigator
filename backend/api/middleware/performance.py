import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.db import connection
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor and optimize request performance.
    Tracks response times and sends real-time updates via WebSocket.
    """
    
    def process_request(self, request):
        """Mark request start time."""
        request._start_time = time.time()
        request._query_count_start = len(connection.queries)
        return None
    
    def process_response(self, request, response):
        """Calculate and log request performance metrics."""
        if hasattr(request, '_start_time'):
            # Calculate metrics
            duration = (time.time() - request._start_time) * 1000  # in milliseconds
            query_count = len(connection.queries) - getattr(request, '_query_count_start', 0)
            
            # Log slow requests
            if duration > 500:  # Log requests taking more than 500ms
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}ms with {query_count} queries"
                )
            
            # Cache performance metrics for analytics
            cache_key = f"perf_metrics:{request.path}:{request.method}"
            metrics = cache.get(cache_key, {
                'count': 0,
                'total_time': 0,
                'max_time': 0,
                'min_time': float('inf'),
                'avg_queries': 0
            })
            
            metrics['count'] += 1
            metrics['total_time'] += duration
            metrics['max_time'] = max(metrics['max_time'], duration)
            metrics['min_time'] = min(metrics['min_time'], duration)
            metrics['avg_queries'] = (
                (metrics['avg_queries'] * (metrics['count'] - 1) + query_count) / 
                metrics['count']
            )
            
            cache.set(cache_key, metrics, 3600)  # Cache for 1 hour
            
            # Add performance headers
            response['X-Response-Time'] = f"{duration:.2f}ms"
            response['X-DB-Query-Count'] = str(query_count)
            
            # Send real-time performance update if it's a search request
            if '/api/search/' in request.path and duration > 100:
                self._send_performance_update(request, duration, query_count)
        
        return response
    
    def _send_performance_update(self, request, duration, query_count):
        """Send performance metrics via WebSocket."""
        try:
            channel_layer = get_channel_layer()
            session_id = request.headers.get('X-Session-ID', '')
            
            if session_id:
                async_to_sync(channel_layer.group_send)(
                    f'search_{session_id}',
                    {
                        'type': 'performance_update',
                        'duration': duration,
                        'query_count': query_count,
                        'path': request.path,
                        'timestamp': time.time()
                    }
                )
        except Exception as e:
            logger.error(f"Error sending performance update: {e}")


class DatabaseQueryOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware to log and optimize database queries.
    """
    
    def process_request(self, request):
        """Reset query log for this request."""
        request._queries = []
        return None
    
    def process_response(self, request, response):
        """Analyze database queries for optimization opportunities."""
        if hasattr(request, '_queries') and len(connection.queries) > 10:
            # Log requests with many queries
            queries = connection.queries[getattr(request, '_query_count_start', 0):]
            
            # Detect N+1 query problems
            query_patterns = {}
            for query in queries:
                sql = query['sql']
                # Extract table name (simple pattern matching)
                if 'FROM' in sql:
                    table = sql.split('FROM')[1].split()[0].strip('`"')
                    query_patterns[table] = query_patterns.get(table, 0) + 1
            
            # Log potential N+1 problems
            for table, count in query_patterns.items():
                if count > 5:
                    logger.warning(
                        f"Potential N+1 query problem: {count} queries to {table} "
                        f"in {request.method} {request.path}"
                    )
        
        return response


class CacheWarmingMiddleware(MiddlewareMixin):
    """
    Middleware to pre-warm caches for common queries.
    """
    
    def process_request(self, request):
        """Warm up caches for common search patterns."""
        if request.path.startswith('/api/search/') and request.method == 'GET':
            # Pre-fetch common query suggestions
            cache_key = 'popular_queries:10:None'
            if not cache.get(cache_key):
                # This would trigger the cache to be populated
                pass
        
        return None