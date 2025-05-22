"""
Celery tasks for analytics data processing and aggregation.
Scheduled tasks for metrics calculation, report generation, and data cleanup.
"""

from celery import shared_task
from django.utils import timezone
import datetime
import logging

from .aggregator import MetricsAggregator
from .models import SystemMetric, UserActivityLog, AuditEvent

logger = logging.getLogger(__name__)


@shared_task
def aggregate_daily_metrics(date_str=None):
    """
    Aggregate metrics for a specific day.
    If date_str is None, aggregates for the previous day.
    Format: YYYY-MM-DD
    """
    try:
        if date_str:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            # Default to yesterday
            date = (timezone.now() - datetime.timedelta(days=1)).date()
        
        # Run aggregations
        daily_agg = MetricsAggregator.aggregate_daily_metrics(date)
        MetricsAggregator.aggregate_query_types(date)
        
        logger.info(f"Successfully aggregated metrics for {date}: {daily_agg.total_queries} queries, {daily_agg.unique_users} users")
        return f"Metrics aggregated for {date}"
    except Exception as e:
        logger.error(f"Error aggregating metrics: {str(e)}")
        raise


@shared_task
def cleanup_old_metrics(days_to_keep=90):
    """
    Clean up old raw metrics data to prevent database bloat.
    Keeps aggregated data but removes raw metrics older than days_to_keep.
    """
    try:
        cutoff_date = timezone.now() - datetime.timedelta(days=days_to_keep)
        
        # Delete old system metrics
        old_metrics = SystemMetric.objects.filter(timestamp__lt=cutoff_date)
        metrics_count = old_metrics.count()
        old_metrics.delete()
        
        # Delete old activity logs
        old_logs = UserActivityLog.objects.filter(timestamp__lt=cutoff_date)
        logs_count = old_logs.count()
        old_logs.delete()
        
        logger.info(f"Cleaned up {metrics_count} old metrics and {logs_count} activity logs")
        return f"Cleaned up {metrics_count} metrics and {logs_count} logs"
    except Exception as e:
        logger.error(f"Error cleaning up old metrics: {str(e)}")
        raise


@shared_task
def generate_weekly_report():
    """
    Generate a weekly analytics report.
    Aggregates data for the past week and prepares summary data.
    """
    try:
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=7)
        
        # Ensure all daily aggregates are calculated
        for i in range(7):
            date = end_date - datetime.timedelta(days=i)
            MetricsAggregator.aggregate_daily_metrics(date)
            MetricsAggregator.aggregate_query_types(date)
        
        # Generate summary
        summary = MetricsAggregator.get_dashboard_summary(days=7)
        
        logger.info(f"Generated weekly report: {summary['total_queries']} queries, {summary['total_unique_users']} users")
        return "Weekly report generated successfully"
    except Exception as e:
        logger.error(f"Error generating weekly report: {str(e)}")
        raise


@shared_task
def monitor_system_performance():
    """
    Collect system performance metrics and check component health.
    Records current CPU, memory usage, and other system metrics.
    """
    try:
        from .monitor import SystemMonitor
        
        # Collect system metrics
        metrics = SystemMonitor.collect_system_metrics()
        
        # Check component health
        health_results = SystemMonitor.check_all_components()
        
        # Log results
        cpu_metric = next((m for m in metrics if m.metric_type == 'cpu_usage'), None)
        memory_metric = next((m for m in metrics if m.metric_type == 'memory_usage'), None)
        
        cpu_value = cpu_metric.value if cpu_metric else 'unknown'
        memory_value = memory_metric.value if memory_metric else 'unknown'
        
        # Count components by status
        status_counts = {}
        for component, result in health_results.items():
            status = result['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        logger.info(f"Recorded system metrics: CPU {cpu_value}%, Memory {memory_value}%")
        logger.info(f"Component health: {status_counts}")
        
        return {
            "metrics_count": len(metrics),
            "component_status": status_counts
        }
    except ImportError as e:
        logger.warning(f"Import error in system monitoring: {e}")
        return f"Import error: {str(e)}"
    except Exception as e:
        logger.error(f"Error monitoring system performance: {str(e)}")
        raise