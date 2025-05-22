"""
System monitoring utilities for the analytics dashboard.
Collects system metrics and tracks component health status.
"""

import os
import time
import logging
import psutil
import socket
from django.utils import timezone
from django.conf import settings
import multiprocessing
import threading
import traceback

from .models import SystemMetric, SystemStatusLog

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Monitors system performance and status.
    Provides methods for checking component health and collecting metrics.
    """
    
    @classmethod
    def collect_system_metrics(cls):
        """Collect and store various system performance metrics"""
        metrics = []
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(
                SystemMetric(
                    metric_type='cpu_usage',
                    value=cpu_percent,
                    unit='%'
                )
            )
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append(
                SystemMetric(
                    metric_type='memory_usage',
                    value=memory.percent,
                    unit='%',
                    metadata={
                        'total': memory.total,
                        'available': memory.available,
                        'used': memory.used,
                    }
                )
            )
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics.append(
                SystemMetric(
                    metric_type='disk_usage',
                    value=disk.percent,
                    unit='%',
                    metadata={
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                    }
                )
            )
            
            # Get process metrics
            process = psutil.Process(os.getpid())
            
            # Process memory usage
            process_memory = process.memory_info()
            metrics.append(
                SystemMetric(
                    metric_type='process_memory',
                    value=process_memory.rss / 1024 / 1024,  # MB
                    unit='MB',
                    metadata={
                        'virtual': process_memory.vms / 1024 / 1024,
                        'percent': process.memory_percent(),
                    }
                )
            )
            
            # Process CPU usage
            process_cpu = process.cpu_percent(interval=0.5)
            metrics.append(
                SystemMetric(
                    metric_type='process_cpu',
                    value=process_cpu,
                    unit='%'
                )
            )
            
            # Number of threads
            num_threads = len(process.threads())
            metrics.append(
                SystemMetric(
                    metric_type='thread_count',
                    value=num_threads,
                    unit='threads'
                )
            )
            
            # Save all metrics
            SystemMetric.objects.bulk_create(metrics)
            return metrics
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return []
    
    @classmethod
    def check_component_status(cls, component_name, check_function):
        """
        Check the status of a system component and record the result.
        
        Args:
            component_name (str): Name of the component to check (from SystemStatusLog.COMPONENT_TYPES)
            check_function (callable): Function that returns (status, message, details)
                where status is one of 'healthy', 'degraded', 'down'
        
        Returns:
            tuple: (success, status, message)
        """
        try:
            status, message, details = check_function()
            
            # Record the status
            SystemStatusLog.objects.create(
                component=component_name,
                status=status,
                message=message,
                details=details or {}
            )
            return True, status, message
        except Exception as e:
            error_msg = f"Error checking {component_name} status: {str(e)}"
            logger.error(error_msg)
            
            # Record the error
            SystemStatusLog.objects.create(
                component=component_name,
                status='down',
                message=error_msg,
                details={'traceback': traceback.format_exc()}
            )
            return False, 'down', error_msg
    
    @classmethod
    def check_api_status(cls):
        """
        Check the API server status.
        
        Returns:
            tuple: (status, message, details)
        """
        # Simple self-check for API (if this code is running, the API is up)
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=0.5)
        memory_percent = process.memory_percent()
        
        details = {
            'pid': os.getpid(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'uptime_seconds': time.time() - process.create_time(),
            'thread_count': len(process.threads()),
        }
        
        # Determine status based on resource usage
        if cpu_percent > 90 or memory_percent > 90:
            return 'degraded', 'API server is under high load', details
        else:
            return 'healthy', 'API server is operating normally', details
    
    @classmethod
    def check_database_status(cls):
        """
        Check the database connection status.
        
        Returns:
            tuple: (status, message, details)
        """
        from django.db import connection
        
        try:
            # Simple query to check connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()[0]
            
            if result == 1:
                # Check connection performance
                start_time = time.time()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                query_time_ms = (time.time() - start_time) * 1000
                
                details = {
                    'query_time_ms': query_time_ms,
                    'connection_info': {
                        'engine': connection.settings_dict['ENGINE'],
                        'name': connection.settings_dict['NAME'],
                        'host': connection.settings_dict['HOST'],
                    }
                }
                
                if query_time_ms > 100:  # More than 100ms is slow
                    return 'degraded', 'Database connection is slow', details
                else:
                    return 'healthy', 'Database connection is healthy', details
            else:
                return 'down', 'Database query returned unexpected result', {}
        except Exception as e:
            return 'down', f'Database connection error: {str(e)}', {'error': str(e)}
    
    @classmethod
    def check_redis_status(cls):
        """
        Check the Redis cache connection status.
        
        Returns:
            tuple: (status, message, details)
        """
        import redis
        from django.core.cache import cache
        
        try:
            # Check if Django cache is using Redis
            if not settings.REDIS_URL:
                return 'down', 'Redis URL not configured', {}
            
            # Connect to Redis directly
            redis_client = redis.Redis.from_url(settings.REDIS_URL)
            
            # Check connectivity with a ping
            start_time = time.time()
            ping_result = redis_client.ping()
            ping_time_ms = (time.time() - start_time) * 1000
            
            if ping_result:
                # Get some Redis stats
                info = redis_client.info()
                memory_used = info.get('used_memory_human', 'unknown')
                connected_clients = info.get('connected_clients', 'unknown')
                uptime_days = info.get('uptime_in_days', 'unknown')
                
                details = {
                    'ping_time_ms': ping_time_ms,
                    'memory_used': memory_used,
                    'connected_clients': connected_clients,
                    'uptime_days': uptime_days,
                    'version': info.get('redis_version', 'unknown'),
                }
                
                if ping_time_ms > 50:  # More than 50ms is slow
                    return 'degraded', 'Redis connection is slow', details
                else:
                    return 'healthy', 'Redis connection is healthy', details
            else:
                return 'down', 'Redis ping failed', {}
        except Exception as e:
            return 'down', f'Redis connection error: {str(e)}', {'error': str(e)}
    
    @classmethod
    def check_vector_db_status(cls):
        """
        Check the vector database (Weaviate) status.
        
        Returns:
            tuple: (status, message, details)
        """
        from ..ingestion.embeddings_utils import get_weaviate_client
        
        try:
            # Get Weaviate client
            client = get_weaviate_client()
            
            # Check if client is initialized
            if not client:
                return 'down', 'Vector DB client initialization failed', {}
            
            # Check connectivity with a simple meta query
            start_time = time.time()
            meta = client.meta.get()
            query_time_ms = (time.time() - start_time) * 1000
            
            if meta:
                # Extract useful information
                version = meta.get('version', 'unknown')
                objects = 0
                try:
                    # Get total number of objects
                    schema = client.schema.get()
                    for cls in schema.get('classes', []):
                        cls_name = cls.get('class')
                        count_result = client.query.aggregate(cls_name).with_meta_count().do()
                        objects += count_result.get('data', {}).get('Aggregate', {}).get(cls_name, [{}])[0].get('meta', {}).get('count', 0)
                except Exception as e:
                    logger.warning(f"Could not get object count from vector DB: {e}")
                
                details = {
                    'version': version,
                    'query_time_ms': query_time_ms,
                    'total_objects': objects,
                }
                
                if query_time_ms > 200:  # More than 200ms is slow
                    return 'degraded', 'Vector DB connection is slow', details
                else:
                    return 'healthy', 'Vector DB connection is healthy', details
            else:
                return 'down', 'Vector DB meta query failed', {}
        except Exception as e:
            return 'down', f'Vector DB connection error: {str(e)}', {'error': str(e)}
    
    @classmethod
    def check_celery_status(cls):
        """
        Check the Celery worker status.
        
        Returns:
            tuple: (status, message, details)
        """
        from celery.app.control import Control
        from rna_backend.celery import app as celery_app
        
        try:
            # Check if Celery workers are running
            control = Control(celery_app)
            
            # Get active workers
            start_time = time.time()
            workers = control.inspect().active()
            query_time_ms = (time.time() - start_time) * 1000
            
            if workers:
                # Get worker statistics
                stats = control.inspect().stats()
                
                # Count active tasks
                active_tasks = 0
                for worker_name, tasks in control.inspect().active().items():
                    active_tasks += len(tasks)
                
                details = {
                    'workers': list(workers.keys()),
                    'worker_count': len(workers),
                    'active_tasks': active_tasks,
                    'query_time_ms': query_time_ms,
                }
                
                return 'healthy', f'Celery workers active ({len(workers)} workers)', details
            else:
                # Try to check if broker is reachable
                try:
                    connection = celery_app.connection()
                    connection.ensure_connection(max_retries=1)
                    connection.release()
                    return 'degraded', 'Celery broker reachable but no active workers', {'broker_reachable': True}
                except Exception as e:
                    return 'down', 'No Celery workers and broker unreachable', {'broker_error': str(e)}
        except Exception as e:
            return 'down', f'Celery status check error: {str(e)}', {'error': str(e)}
    
    @classmethod
    def check_llm_status(cls):
        """
        Check the Language Model service status.
        
        Returns:
            tuple: (status, message, details)
        """
        from ..offline import get_llm_client, is_offline_mode
        
        try:
            # Get LLM client
            client = get_llm_client()
            
            # Check if client is initialized
            if not client:
                return 'down', 'LLM client initialization failed', {}
            
            # In offline mode, the check is different
            if is_offline_mode():
                # For local models, just check if the client exists
                details = {'mode': 'offline', 'model': settings.LOCAL_LLM_CONFIG.get('model_name', 'unknown')}
                return 'healthy', 'Local LLM service available', details
            else:
                # Try a simple API call
                start_time = time.time()
                try:
                    response = client.models.list()
                    query_time_ms = (time.time() - start_time) * 1000
                    
                    details = {
                        'query_time_ms': query_time_ms,
                        'mode': 'online',
                        'model': settings.OPENAI_MODEL,
                    }
                    
                    if query_time_ms > 1000:  # More than 1 second is slow
                        return 'degraded', 'OpenAI API is responding slowly', details
                    else:
                        return 'healthy', 'OpenAI API is healthy', details
                except Exception as e:
                    # Try simplified test if models.list() is not available
                    try:
                        # Try a very small completion as a connectivity test
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "system", "content": "Say hello."}],
                            max_tokens=1
                        )
                        query_time_ms = (time.time() - start_time) * 1000
                        
                        details = {
                            'query_time_ms': query_time_ms,
                            'mode': 'online',
                            'model': settings.OPENAI_MODEL,
                        }
                        
                        if query_time_ms > 1000:  # More than 1 second is slow
                            return 'degraded', 'OpenAI API is responding slowly', details
                        else:
                            return 'healthy', 'OpenAI API is healthy', details
                    except Exception as inner_e:
                        return 'down', f'OpenAI API error: {str(inner_e)}', {'error': str(inner_e)}
        except Exception as e:
            return 'down', f'LLM service check error: {str(e)}', {'error': str(e)}
    
    @classmethod
    def check_all_components(cls):
        """
        Check status of all system components.
        
        Returns:
            dict: Component status results
        """
        results = {}
        
        # Define components and their check functions
        components = {
            'api': cls.check_api_status,
            'db': cls.check_database_status,
            'redis': cls.check_redis_status,
            'vector_db': cls.check_vector_db_status,
            'celery': cls.check_celery_status,
            'llm': cls.check_llm_status,
        }
        
        # Check each component
        for component, check_func in components.items():
            success, status, message = cls.check_component_status(component, check_func)
            results[component] = {
                'success': success,
                'status': status,
                'message': message,
            }
        
        return results
    
    @classmethod
    def get_system_health_summary(cls):
        """
        Get a summary of system health.
        
        Returns:
            dict: System health summary
        """
        # Get latest status for each component
        latest_statuses = {}
        components = ['api', 'db', 'vector_db', 'celery', 'redis', 'llm']
        
        for component in components:
            try:
                latest = SystemStatusLog.objects.filter(
                    component=component
                ).order_by('-timestamp').first()
                
                if latest:
                    latest_statuses[component] = {
                        'status': latest.status,
                        'message': latest.message,
                        'last_updated': latest.timestamp,
                    }
                else:
                    latest_statuses[component] = {
                        'status': 'unknown',
                        'message': 'No status information available',
                        'last_updated': None,
                    }
            except Exception as e:
                latest_statuses[component] = {
                    'status': 'error',
                    'message': f'Error retrieving status: {str(e)}',
                    'last_updated': None,
                }
        
        # Get latest system metrics
        metrics = {}
        try:
            for metric_type in ['cpu_usage', 'memory_usage', 'disk_usage', 'process_memory', 'process_cpu']:
                latest = SystemMetric.objects.filter(
                    metric_type=metric_type
                ).order_by('-timestamp').first()
                
                if latest:
                    metrics[metric_type] = {
                        'value': latest.value,
                        'unit': latest.unit,
                        'last_updated': latest.timestamp,
                    }
        except Exception as e:
            metrics['error'] = str(e)
        
        # Determine overall system health
        status_scores = {
            'healthy': 2,
            'degraded': 1,
            'down': 0,
            'unknown': -1,
            'error': -1,
        }
        
        component_scores = [status_scores.get(s.get('status', 'unknown'), -1) 
                           for c, s in latest_statuses.items()]
        
        if -1 in component_scores:
            overall_health = 'unknown'
        elif 0 in component_scores:
            overall_health = 'down'
        elif 1 in component_scores:
            overall_health = 'degraded'
        else:
            overall_health = 'healthy'
        
        # Create summary
        summary = {
            'overall_health': overall_health,
            'component_status': latest_statuses,
            'system_metrics': metrics,
            'timestamp': timezone.now(),
        }
        
        return summary


# Background monitoring thread
class BackgroundMonitor:
    """
    Background thread for system monitoring.
    Periodically collects metrics and checks component health.
    """
    
    def __init__(self, interval=300):
        """
        Initialize the background monitor.
        
        Args:
            interval (int): Monitoring interval in seconds (default: 300 = 5 minutes)
        """
        self.interval = interval
        self.stop_event = threading.Event()
        self.thread = None
    
    def start(self):
        """Start the monitoring thread"""
        if self.thread is not None and self.thread.is_alive():
            logger.warning("Background monitor already running")
            return
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Background monitor started (interval: {self.interval}s)")
    
    def stop(self):
        """Stop the monitoring thread"""
        if self.thread is not None:
            self.stop_event.set()
            self.thread.join(timeout=10)
            self.thread = None
            logger.info("Background monitor stopped")
    
    def _run(self):
        """Main monitoring loop"""
        while not self.stop_event.is_set():
            try:
                # Collect system metrics
                SystemMonitor.collect_system_metrics()
                
                # Check component health
                SystemMonitor.check_all_components()
                
                logger.debug("Background monitoring cycle completed")
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
            
            # Wait for the next interval or until stop is requested
            self.stop_event.wait(self.interval)


# Global monitor instance
monitor = None

def start_background_monitoring():
    """Start the background monitoring thread"""
    global monitor
    if monitor is None:
        monitor = BackgroundMonitor()
    monitor.start()

def stop_background_monitoring():
    """Stop the background monitoring thread"""
    global monitor
    if monitor is not None:
        monitor.stop()