"""
Performance monitoring and profiling utilities for RNA Lab Navigator.

This module provides tools for monitoring system performance, identifying bottlenecks,
and generating detailed performance reports for optimization.

Features:
- Real-time performance monitoring
- Memory and CPU profiling
- Database query analysis
- Vector search performance tracking
- Bottleneck identification
- Performance trend analysis
"""

import time
import psutil
import logging
import threading
import json
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
import cProfile
import pstats
import io
from collections import defaultdict, deque
from datetime import datetime, timedelta
import sqlite3
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Container for a single performance metric."""
    timestamp: float
    component: str
    operation: str
    duration: float
    memory_mb: float
    cpu_percent: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemResourceSnapshot:
    """Container for system resource information."""
    timestamp: float
    memory_percent: float
    memory_mb: float
    cpu_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int

class PerformanceProfiler:
    """Main performance profiler for the RNA Lab Navigator system."""
    
    def __init__(self, db_path: str = "performance_metrics.db"):
        self.db_path = db_path
        self.metrics_buffer = deque(maxlen=10000)  # Keep last 10k metrics in memory
        self.system_snapshots = deque(maxlen=1000)  # Keep last 1k system snapshots
        self.monitoring_active = False
        self.monitor_thread = None
        self.component_stats = defaultdict(lambda: {
            'total_calls': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'last_call': 0
        })
        
        # Initialize database
        self._init_database()
        
        # Start system monitoring
        self.start_monitoring()
    
    def _init_database(self):
        """Initialize SQLite database for storing metrics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        component TEXT,
                        operation TEXT,
                        duration REAL,
                        memory_mb REAL,
                        cpu_percent REAL,
                        metadata TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        memory_percent REAL,
                        memory_mb REAL,
                        cpu_percent REAL,
                        disk_usage_percent REAL,
                        network_bytes_sent INTEGER,
                        network_bytes_recv INTEGER,
                        active_connections INTEGER
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_component ON performance_metrics(component)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON system_snapshots(timestamp)")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
    
    def start_monitoring(self, interval: float = 1.0):
        """Start system resource monitoring in background thread."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._system_monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop system resource monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _system_monitor_loop(self, interval: float):
        """Background loop for collecting system metrics."""
        while self.monitoring_active:
            try:
                snapshot = self._capture_system_snapshot()
                self.system_snapshots.append(snapshot)
                
                # Periodically flush to database
                if len(self.system_snapshots) % 100 == 0:
                    self._flush_system_snapshots()
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {str(e)}")
            
            time.sleep(interval)
    
    def _capture_system_snapshot(self) -> SystemResourceSnapshot:
        """Capture current system resource usage."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Count active network connections (simplified)
        try:
            connections = len(psutil.net_connections())
        except:
            connections = 0
        
        return SystemResourceSnapshot(
            timestamp=time.time(),
            memory_percent=memory.percent,
            memory_mb=memory.used / (1024 * 1024),
            cpu_percent=cpu_percent,
            disk_usage_percent=disk.percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            active_connections=connections
        )
    
    def _flush_system_snapshots(self):
        """Flush system snapshots to database."""
        if not self.system_snapshots:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                snapshots_to_save = list(self.system_snapshots)
                self.system_snapshots.clear()
                
                for snapshot in snapshots_to_save:
                    conn.execute("""
                        INSERT INTO system_snapshots 
                        (timestamp, memory_percent, memory_mb, cpu_percent, 
                         disk_usage_percent, network_bytes_sent, network_bytes_recv, active_connections)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot.timestamp, snapshot.memory_percent, snapshot.memory_mb,
                        snapshot.cpu_percent, snapshot.disk_usage_percent,
                        snapshot.network_bytes_sent, snapshot.network_bytes_recv,
                        snapshot.active_connections
                    ))
                
        except Exception as e:
            logger.error(f"Failed to flush system snapshots: {str(e)}")
    
    def record_metric(self, component: str, operation: str, duration: float, 
                     metadata: Dict[str, Any] = None):
        """Record a performance metric."""
        # Get current system info
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        metric = PerformanceMetric(
            timestamp=time.time(),
            component=component,
            operation=operation,
            duration=duration,
            memory_mb=memory_info.used / (1024 * 1024),
            cpu_percent=cpu_percent,
            metadata=metadata or {}
        )
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        
        # Update component statistics
        stats = self.component_stats[f"{component}.{operation}"]
        stats['total_calls'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['total_calls']
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        stats['last_call'] = time.time()
        
        # Periodically flush to database
        if len(self.metrics_buffer) % 100 == 0:
            self._flush_metrics()
    
    def _flush_metrics(self):
        """Flush metrics buffer to database."""
        if not self.metrics_buffer:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                metrics_to_save = list(self.metrics_buffer)
                self.metrics_buffer.clear()
                
                for metric in metrics_to_save:
                    conn.execute("""
                        INSERT INTO performance_metrics 
                        (timestamp, component, operation, duration, memory_mb, cpu_percent, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metric.timestamp, metric.component, metric.operation,
                        metric.duration, metric.memory_mb, metric.cpu_percent,
                        json.dumps(metric.metadata)
                    ))
                
        except Exception as e:
            logger.error(f"Failed to flush metrics: {str(e)}")
    
    @contextmanager
    def measure(self, component: str, operation: str, metadata: Dict[str, Any] = None):
        """Context manager for measuring operation performance."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric(component, operation, duration, metadata)
    
    def profile_function(self, component: str = None):
        """Decorator for profiling function performance."""
        def decorator(func: Callable):
            comp = component or func.__module__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.measure(comp, func.__name__):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def profile_with_cprofile(self, component: str, operation: str):
        """Context manager that provides detailed cProfile analysis."""
        @contextmanager
        def profiler():
            pr = cProfile.Profile()
            pr.enable()
            start_time = time.time()
            
            try:
                yield pr
            finally:
                pr.disable()
                duration = time.time() - start_time
                
                # Get profiling stats
                stats_stream = io.StringIO()
                ps = pstats.Stats(pr, stream=stats_stream)
                ps.sort_stats('cumulative')
                ps.print_stats(20)  # Top 20 functions
                
                # Record metric with profiling data
                self.record_metric(component, operation, duration, {
                    'profile_stats': stats_stream.getvalue(),
                    'function_calls': ps.total_calls
                })
        
        return profiler()
    
    def get_component_performance(self, component: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics for a specific component."""
        since = time.time() - (hours * 3600)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT operation, duration, timestamp, metadata
                    FROM performance_metrics
                    WHERE component = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (component, since))
                
                metrics = cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Failed to query component performance: {str(e)}")
            return {}
        
        if not metrics:
            return {"error": "No metrics found"}
        
        # Analyze metrics
        operations = defaultdict(list)
        for operation, duration, timestamp, metadata_str in metrics:
            operations[operation].append({
                'duration': duration,
                'timestamp': timestamp,
                'metadata': json.loads(metadata_str) if metadata_str else {}
            })
        
        result = {}
        for operation, data in operations.items():
            durations = [d['duration'] for d in data]
            result[operation] = {
                'count': len(durations),
                'mean_duration': statistics.mean(durations),
                'median_duration': statistics.median(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'p95_duration': statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations),
                'total_time': sum(durations),
                'latest_call': max(d['timestamp'] for d in data)
            }
        
        return result
    
    def get_system_health(self, minutes: int = 60) -> Dict[str, Any]:
        """Get system health metrics for the specified time period."""
        since = time.time() - (minutes * 60)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT memory_percent, memory_mb, cpu_percent, disk_usage_percent
                    FROM system_snapshots
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (since,))
                
                snapshots = cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Failed to query system health: {str(e)}")
            return {}
        
        if not snapshots:
            return {"error": "No system snapshots found"}
        
        # Analyze system metrics
        memory_percents = [s[0] for s in snapshots]
        memory_mbs = [s[1] for s in snapshots]
        cpu_percents = [s[2] for s in snapshots]
        disk_percents = [s[3] for s in snapshots]
        
        return {
            'memory': {
                'current_percent': memory_percents[0] if memory_percents else 0,
                'avg_percent': statistics.mean(memory_percents),
                'max_percent': max(memory_percents),
                'current_mb': memory_mbs[0] if memory_mbs else 0,
                'avg_mb': statistics.mean(memory_mbs),
                'max_mb': max(memory_mbs)
            },
            'cpu': {
                'current_percent': cpu_percents[0] if cpu_percents else 0,
                'avg_percent': statistics.mean(cpu_percents),
                'max_percent': max(cpu_percents)
            },
            'disk': {
                'current_percent': disk_percents[0] if disk_percents else 0,
                'avg_percent': statistics.mean(disk_percents),
                'max_percent': max(disk_percents)
            },
            'sample_count': len(snapshots)
        }
    
    def identify_bottlenecks(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks in the system."""
        since = time.time() - (hours * 3600)
        bottlenecks = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Find slow operations (>5s for regular, >8s for complex)
                cursor = conn.execute("""
                    SELECT component, operation, AVG(duration) as avg_duration, 
                           COUNT(*) as call_count, MAX(duration) as max_duration
                    FROM performance_metrics
                    WHERE timestamp >= ? AND duration > 5.0
                    GROUP BY component, operation
                    HAVING call_count > 1
                    ORDER BY avg_duration DESC
                """, (since,))
                
                slow_operations = cursor.fetchall()
                
                for comp, op, avg_dur, count, max_dur in slow_operations:
                    bottlenecks.append({
                        'type': 'slow_operation',
                        'component': comp,
                        'operation': op,
                        'avg_duration': avg_dur,
                        'max_duration': max_dur,
                        'call_count': count,
                        'severity': 'high' if avg_dur > 8.0 else 'medium'
                    })
                
                # Find frequently called operations
                cursor = conn.execute("""
                    SELECT component, operation, COUNT(*) as call_count, 
                           AVG(duration) as avg_duration
                    FROM performance_metrics
                    WHERE timestamp >= ?
                    GROUP BY component, operation
                    HAVING call_count > 100
                    ORDER BY call_count DESC
                    LIMIT 10
                """, (since,))
                
                frequent_operations = cursor.fetchall()
                
                for comp, op, count, avg_dur in frequent_operations:
                    if avg_dur > 1.0:  # Frequently called and slow
                        bottlenecks.append({
                            'type': 'frequent_slow_operation',
                            'component': comp,
                            'operation': op,
                            'call_count': count,
                            'avg_duration': avg_dur,
                            'total_time': count * avg_dur,
                            'severity': 'high' if count * avg_dur > 1000 else 'medium'
                        })
                
        except Exception as e:
            logger.error(f"Failed to identify bottlenecks: {str(e)}")
        
        # Check system resource bottlenecks
        system_health = self.get_system_health(minutes=hours*60)
        if system_health and 'memory' in system_health:
            if system_health['memory']['max_percent'] > 85:
                bottlenecks.append({
                    'type': 'memory_pressure',
                    'max_usage': system_health['memory']['max_percent'],
                    'avg_usage': system_health['memory']['avg_percent'],
                    'severity': 'high' if system_health['memory']['max_percent'] > 95 else 'medium'
                })
            
            if system_health['cpu']['max_percent'] > 80:
                bottlenecks.append({
                    'type': 'cpu_pressure',
                    'max_usage': system_health['cpu']['max_percent'],
                    'avg_usage': system_health['cpu']['avg_percent'],
                    'severity': 'high' if system_health['cpu']['max_percent'] > 95 else 'medium'
                })
        
        return bottlenecks
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization recommendations."""
        bottlenecks = self.identify_bottlenecks()
        system_health = self.get_system_health()
        
        # Component analysis
        component_perf = {}
        components = ['api.search', 'api.rag', 'api.ingestion', 'api.llm']
        for comp in components:
            component_perf[comp] = self.get_component_performance(comp)
        
        recommendations = []
        
        # Analyze bottlenecks and generate recommendations
        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'slow_operation':
                if 'search' in bottleneck['component']:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'search_optimization',
                        'description': f"Optimize {bottleneck['operation']} in {bottleneck['component']}",
                        'suggestions': [
                            'Implement result caching',
                            'Optimize vector search parameters',
                            'Consider index optimization',
                            'Review hybrid search alpha parameter'
                        ],
                        'expected_improvement': f"Reduce {bottleneck['avg_duration']:.2f}s to <2s"
                    })
                
                elif 'rag' in bottleneck['component']:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'rag_optimization',
                        'description': f"Optimize RAG pipeline {bottleneck['operation']}",
                        'suggestions': [
                            'Implement chunk caching',
                            'Optimize reranking parameters',
                            'Consider parallel processing',
                            'Review context size limits'
                        ],
                        'expected_improvement': f"Reduce {bottleneck['avg_duration']:.2f}s to <3s"
                    })
                
                elif 'llm' in bottleneck['component']:
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'llm_optimization',
                        'description': f"Optimize LLM {bottleneck['operation']}",
                        'suggestions': [
                            'Implement response caching',
                            'Optimize prompt templates',
                            'Consider smaller models for simple queries',
                            'Implement streaming responses'
                        ],
                        'expected_improvement': f"Reduce {bottleneck['avg_duration']:.2f}s to <4s"
                    })
            
            elif bottleneck['type'] == 'memory_pressure':
                recommendations.append({
                    'priority': 'high',
                    'category': 'memory_optimization',
                    'description': 'High memory usage detected',
                    'suggestions': [
                        'Implement object pooling',
                        'Optimize data structures',
                        'Clear unused caches',
                        'Review memory leaks',
                        'Consider vertical scaling'
                    ],
                    'expected_improvement': f"Reduce memory usage from {bottleneck['max_usage']:.1f}% to <80%"
                })
            
            elif bottleneck['type'] == 'cpu_pressure':
                recommendations.append({
                    'priority': 'high',
                    'category': 'cpu_optimization',
                    'description': 'High CPU usage detected',
                    'suggestions': [
                        'Implement async processing',
                        'Optimize algorithms',
                        'Use CPU profiling tools',
                        'Consider horizontal scaling',
                        'Review computational bottlenecks'
                    ],
                    'expected_improvement': f"Reduce CPU usage from {bottleneck['max_usage']:.1f}% to <70%"
                })
        
        # General recommendations based on KPI targets
        if not any(r['category'] == 'caching' for r in recommendations):
            recommendations.append({
                'priority': 'medium',
                'category': 'caching',
                'description': 'Implement comprehensive caching strategy',
                'suggestions': [
                    'Cache frequent queries',
                    'Cache vector search results',
                    'Cache LLM responses',
                    'Implement Redis for distributed caching'
                ],
                'expected_improvement': 'Reduce average response time by 30-50%'
            })
        
        return {
            'timestamp': time.time(),
            'bottlenecks': bottlenecks,
            'system_health': system_health,
            'component_performance': component_perf,
            'recommendations': recommendations,
            'kpi_status': {
                'target_median_latency': 5.0,
                'current_performance': 'needs_analysis',  # Would need recent query data
                'compliance_rate': 'unknown'  # Would need recent query data
            }
        }
    
    def cleanup(self):
        """Cleanup resources and save remaining data."""
        self.stop_monitoring()
        self._flush_metrics()
        self._flush_system_snapshots()
        logger.info("Performance profiler cleanup completed")


# Global profiler instance
_global_profiler = None

def get_profiler() -> PerformanceProfiler:
    """Get the global performance profiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler

def profile(component: str = None):
    """Decorator for profiling function performance."""
    return get_profiler().profile_function(component)

@contextmanager
def measure(component: str, operation: str, metadata: Dict[str, Any] = None):
    """Context manager for measuring operation performance."""
    with get_profiler().measure(component, operation, metadata):
        yield


# Django integration
try:
    from django.core.management.base import BaseCommand
    
    class Command(BaseCommand):
        """Django management command for performance analysis."""
        help = 'Analyze system performance and generate optimization report'
        
        def add_arguments(self, parser):
            parser.add_argument('--hours', type=int, default=24,
                              help='Hours of data to analyze')
            parser.add_argument('--output', type=str,
                              help='Output file for JSON report')
        
        def handle(self, *args, **options):
            profiler = get_profiler()
            
            self.stdout.write("Generating performance analysis report...")
            
            report = profiler.generate_optimization_report()
            
            if options['output']:
                with open(options['output'], 'w') as f:
                    json.dump(report, f, indent=2)
                self.stdout.write(f"Report saved to {options['output']}")
            else:
                self.stdout.write(json.dumps(report, indent=2))
            
            # Print summary
            bottlenecks = report.get('bottlenecks', [])
            recommendations = report.get('recommendations', [])
            
            self.stdout.write(f"\nSummary:")
            self.stdout.write(f"  - Found {len(bottlenecks)} bottlenecks")
            self.stdout.write(f"  - Generated {len(recommendations)} recommendations")
            
            high_priority = len([r for r in recommendations if r.get('priority') == 'high'])
            if high_priority > 0:
                self.stdout.write(self.style.WARNING(
                    f"  - {high_priority} high-priority optimizations needed"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    "  - No critical performance issues found"
                ))

except ImportError:
    # Django not available
    pass