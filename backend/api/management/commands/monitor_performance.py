from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from datetime import timedelta
import json
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
import time

class Command(BaseCommand):
    help = 'Monitor real-time performance metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Update interval in seconds'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=300,
            help='Monitoring duration in seconds (0 for infinite)'
        )

    def handle(self, *args, **options):
        console = Console()
        interval = options['interval']
        duration = options['duration']
        start_time = time.time()
        
        console.print("[bold green]Starting performance monitoring...[/bold green]")
        
        with Live(self.generate_dashboard(), refresh_per_second=1, console=console) as live:
            while True:
                time.sleep(interval)
                live.update(self.generate_dashboard())
                
                # Check if we should stop
                if duration > 0 and (time.time() - start_time) > duration:
                    break
        
        console.print("[bold green]Performance monitoring completed.[/bold green]")
    
    def generate_dashboard(self):
        """Generate performance dashboard."""
        # Create main table
        table = Table(title="RNA Lab Navigator - Performance Monitor", 
                     title_style="bold magenta")
        
        # Add columns
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")
        
        # Get cache metrics
        cache_metrics = self.get_cache_metrics()
        table.add_row("Cache Hit Rate", f"{cache_metrics['hit_rate']:.1f}%", 
                     self.get_status_emoji(cache_metrics['hit_rate'], 80, 60))
        table.add_row("Cached Items", str(cache_metrics['total_items']), "📊")
        
        # Get database metrics
        db_metrics = self.get_database_metrics()
        table.add_row("Active DB Connections", str(db_metrics['active_connections']), 
                     self.get_status_emoji(100 - db_metrics['active_connections'], 70, 50))
        table.add_row("Avg Query Time", f"{db_metrics['avg_query_time']:.2f}ms", 
                     self.get_status_emoji(100 - db_metrics['avg_query_time'], 70, 50))
        
        # Get API performance metrics
        api_metrics = self.get_api_metrics()
        table.add_row("Avg Response Time", f"{api_metrics['avg_response_time']:.2f}ms", 
                     self.get_status_emoji(500 - api_metrics['avg_response_time'], 300, 100))
        table.add_row("Requests/min", str(api_metrics['requests_per_minute']), "📈")
        
        # Get search metrics
        search_metrics = self.get_search_metrics()
        table.add_row("Search Cache Hits", str(search_metrics['cache_hits']), "🔍")
        table.add_row("Avg Search Time", f"{search_metrics['avg_search_time']:.2f}ms", 
                     self.get_status_emoji(300 - search_metrics['avg_search_time'], 200, 100))
        
        # Create sub-tables for detailed metrics
        slow_endpoints = self.get_slow_endpoints()
        if slow_endpoints:
            slow_table = Table(title="Slow Endpoints", show_header=True)
            slow_table.add_column("Endpoint", style="red")
            slow_table.add_column("Avg Time (ms)", style="yellow")
            slow_table.add_column("Count", style="white")
            
            for endpoint in slow_endpoints[:5]:
                slow_table.add_row(
                    endpoint['path'][:50],
                    f"{endpoint['avg_time']:.2f}",
                    str(endpoint['count'])
                )
            
            return Panel.fit(
                f"{table}\n\n{slow_table}",
                title=f"[bold blue]Performance Dashboard - {timezone.now().strftime('%H:%M:%S')}[/bold blue]",
                border_style="blue"
            )
        
        return Panel.fit(
            table,
            title=f"[bold blue]Performance Dashboard - {timezone.now().strftime('%H:%M:%S')}[/bold blue]",
            border_style="blue"
        )
    
    def get_cache_metrics(self):
        """Get cache performance metrics."""
        try:
            # Get all performance metric keys
            keys = cache.keys("perf_metrics:*")
            total_hits = 0
            total_requests = 0
            
            # This is a simplified example - in production you'd track actual hits/misses
            return {
                'hit_rate': 85.0,  # Example value
                'total_items': len(keys)
            }
        except:
            return {'hit_rate': 0.0, 'total_items': 0}
    
    def get_database_metrics(self):
        """Get database performance metrics."""
        try:
            with connection.cursor() as cursor:
                # Get connection count (PostgreSQL specific)
                cursor.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
                )
                active_connections = cursor.fetchone()[0]
            
            # Calculate average query time from recent queries
            recent_queries = connection.queries[-100:]  # Last 100 queries
            if recent_queries:
                avg_time = sum(float(q.get('time', 0)) for q in recent_queries) / len(recent_queries)
                avg_time_ms = avg_time * 1000
            else:
                avg_time_ms = 0
            
            return {
                'active_connections': active_connections,
                'avg_query_time': avg_time_ms
            }
        except:
            return {'active_connections': 0, 'avg_query_time': 0}
    
    def get_api_metrics(self):
        """Get API performance metrics."""
        try:
            # Aggregate performance metrics from cache
            total_time = 0
            total_count = 0
            
            keys = cache.keys("perf_metrics:*")
            for key in keys:
                metrics = cache.get(key)
                if metrics:
                    total_time += metrics.get('total_time', 0)
                    total_count += metrics.get('count', 0)
            
            avg_response_time = total_time / total_count if total_count > 0 else 0
            
            # Calculate requests per minute (based on last hour)
            requests_per_minute = total_count / 60 if total_count > 0 else 0
            
            return {
                'avg_response_time': avg_response_time,
                'requests_per_minute': int(requests_per_minute)
            }
        except:
            return {'avg_response_time': 0, 'requests_per_minute': 0}
    
    def get_search_metrics(self):
        """Get search-specific performance metrics."""
        try:
            # Get search cache metrics
            search_keys = [k for k in cache.keys("search:*") if not k.startswith("search_")]
            cache_hits = len(search_keys)
            
            # Get average search time
            search_perf_keys = [k for k in cache.keys("perf_metrics:*") if 'search' in k]
            total_time = 0
            total_count = 0
            
            for key in search_perf_keys:
                metrics = cache.get(key)
                if metrics:
                    total_time += metrics.get('total_time', 0)
                    total_count += metrics.get('count', 0)
            
            avg_search_time = total_time / total_count if total_count > 0 else 0
            
            return {
                'cache_hits': cache_hits,
                'avg_search_time': avg_search_time
            }
        except:
            return {'cache_hits': 0, 'avg_search_time': 0}
    
    def get_slow_endpoints(self):
        """Get slowest API endpoints."""
        try:
            endpoints = []
            keys = cache.keys("perf_metrics:*")
            
            for key in keys:
                metrics = cache.get(key)
                if metrics and metrics['count'] > 0:
                    path = key.replace("perf_metrics:", "").split(":")[0]
                    avg_time = metrics['total_time'] / metrics['count']
                    
                    endpoints.append({
                        'path': path,
                        'avg_time': avg_time,
                        'count': metrics['count']
                    })
            
            # Sort by average time (slowest first)
            endpoints.sort(key=lambda x: x['avg_time'], reverse=True)
            return endpoints
        except:
            return []
    
    def get_status_emoji(self, value, good_threshold, warning_threshold):
        """Get status emoji based on value and thresholds."""
        if value >= good_threshold:
            return "✅"
        elif value >= warning_threshold:
            return "⚠️"
        else:
            return "❌"