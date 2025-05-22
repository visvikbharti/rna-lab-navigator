"""
Django management command to monitor system health.
Checks component status and collects performance metrics.
"""

from django.core.management.base import BaseCommand
from api.analytics.monitor import SystemMonitor, start_background_monitoring, stop_background_monitoring
import json
import time


class Command(BaseCommand):
    help = "Monitor system health and collect performance metrics"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Run in watch mode, continuously monitoring system health'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds for watch mode (default: 60)'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Start background monitoring daemon'
        )
        parser.add_argument(
            '--stop-daemon',
            action='store_true',
            help='Stop background monitoring daemon'
        )
        parser.add_argument(
            '--metrics-only',
            action='store_true',
            help='Collect metrics only, without checking component status'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results as JSON'
        )
        
    def handle(self, *args, **options):
        # Handle daemon mode
        if options['daemon']:
            start_background_monitoring()
            self.stdout.write(self.style.SUCCESS("Background monitoring started"))
            return
        
        if options['stop_daemon']:
            stop_background_monitoring()
            self.stdout.write(self.style.SUCCESS("Background monitoring stopped"))
            return
        
        # Handle watch mode
        if options['watch']:
            try:
                interval = options['interval']
                self.stdout.write(f"Running in watch mode (Ctrl+C to stop, interval: {interval}s)")
                self.stdout.write("=" * 50)
                
                cycle = 1
                while True:
                    self.stdout.write(f"\nCycle {cycle} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
                    self.stdout.write("-" * 50)
                    
                    # Run the checks
                    self._run_monitoring(options)
                    
                    # Wait for the next cycle
                    self.stdout.write(f"Waiting {interval} seconds...")
                    time.sleep(interval)
                    cycle += 1
            except KeyboardInterrupt:
                self.stdout.write("\nWatch mode terminated by user")
                return
        
        # One-time run
        self._run_monitoring(options)
    
    def _run_monitoring(self, options):
        if options['metrics_only']:
            # Collect and output metrics only
            metrics = SystemMonitor.collect_system_metrics()
            if options['json']:
                self.stdout.write(json.dumps(
                    [{"metric_type": m.metric_type, "value": m.value, "unit": m.unit} for m in metrics],
                    indent=2
                ))
            else:
                self.stdout.write("System Metrics:")
                for metric in metrics:
                    self.stdout.write(f"  {metric.metric_type}: {metric.value} {metric.unit}")
        else:
            # Check all components and output results
            results = SystemMonitor.check_all_components()
            
            if options['json']:
                self.stdout.write(json.dumps(results, indent=2))
            else:
                self.stdout.write("Component Status:")
                for component, result in results.items():
                    status = result['status']
                    message = result['message']
                    
                    if status == 'healthy':
                        status_style = self.style.SUCCESS(status)
                    elif status == 'degraded':
                        status_style = self.style.WARNING(status)
                    else:
                        status_style = self.style.ERROR(status)
                        
                    self.stdout.write(f"  {component}: {status_style} - {message}")
            
            # Also collect metrics
            SystemMonitor.collect_system_metrics()
            
            # Output summary
            summary = SystemMonitor.get_system_health_summary()
            overall = summary['overall_health']
            
            if options['json']:
                self.stdout.write(json.dumps(summary, indent=2))
            else:
                if overall == 'healthy':
                    overall_style = self.style.SUCCESS(overall)
                elif overall == 'degraded':
                    overall_style = self.style.WARNING(overall)
                else:
                    overall_style = self.style.ERROR(overall)
                
                self.stdout.write(f"\nOverall System Health: {overall_style}")
                
                # Show current resource usage
                self.stdout.write("\nCurrent Resource Usage:")
                for metric_name, metric_data in summary['system_metrics'].items():
                    if isinstance(metric_data, dict) and 'value' in metric_data:
                        self.stdout.write(f"  {metric_name}: {metric_data['value']} {metric_data['unit']}")