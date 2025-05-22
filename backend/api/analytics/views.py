"""
Views for the analytics API endpoints.
Provides data for the dashboard and analytics visualization.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import user_passes_test
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
import datetime
import json

from .models import (
    SystemMetric,
    AuditEvent,
    UserActivityLog,
    DailyMetricAggregate,
    QueryTypeAggregate,
    SecurityEvent
)
from .aggregator import MetricsAggregator


class DashboardDataView(APIView):
    """
    API view for retrieving dashboard data.
    Provides aggregated metrics for the dashboard visualization.
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get dashboard data for the specified time period"""
        days = int(request.query_params.get('days', 30))
        
        # Get dashboard summary
        summary = MetricsAggregator.get_dashboard_summary(days=days)
        
        return Response(summary)


@require_GET
@user_passes_test(lambda u: u.is_staff)
def system_health_view(request):
    """
    View for system health metrics.
    Provides current system status and performance metrics.
    """
    # Time range for recent metrics
    end_time = timezone.now()
    start_time = end_time - datetime.timedelta(hours=6)
    
    # Get recent system metrics
    cpu_metrics = SystemMetric.objects.filter(
        metric_type='cpu_usage',
        timestamp__gte=start_time,
        timestamp__lte=end_time
    ).order_by('timestamp')
    
    memory_metrics = SystemMetric.objects.filter(
        metric_type='memory_usage',
        timestamp__gte=start_time,
        timestamp__lte=end_time
    ).order_by('timestamp')
    
    # Format data for charts
    cpu_data = [
        {
            'timestamp': metric.timestamp.strftime('%Y-%m-%d %H:%M'),
            'value': metric.value
        }
        for metric in cpu_metrics
    ]
    
    memory_data = [
        {
            'timestamp': metric.timestamp.strftime('%Y-%m-%d %H:%M'),
            'value': metric.value
        }
        for metric in memory_metrics
    ]
    
    # Get latest metrics for each system component
    component_statuses = {}
    for component in ['api', 'db', 'vector_db', 'celery', 'redis', 'llm', 'embedding']:
        status = SystemStatusLog.objects.filter(component=component).order_by('-timestamp').first()
        if status:
            component_statuses[component] = {
                'status': status.status,
                'message': status.message,
                'updated': status.timestamp.strftime('%Y-%m-%d %H:%M')
            }
    
    return JsonResponse({
        'cpu': cpu_data,
        'memory': memory_data,
        'components': component_statuses
    })


@require_GET
@user_passes_test(lambda u: u.is_staff)
def query_analytics_view(request):
    """
    View for query analytics data.
    Provides insights into query patterns and categories.
    """
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - datetime.timedelta(days=days-1)
    
    # Get query type distribution
    query_types = QueryTypeAggregate.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).values('category').annotate(
        total=Sum('count')
    ).order_by('-total')
    
    # Get daily query counts
    daily_queries = DailyMetricAggregate.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).values('date', 'total_queries')
    
    # Format data for response
    return JsonResponse({
        'query_types': list(query_types),
        'daily_queries': list(daily_queries),
        'period': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'days': days
        }
    })


@require_GET
@user_passes_test(lambda u: u.is_staff)
def security_analytics_view(request):
    """
    View for security analytics data.
    Provides insights into security events and issues.
    """
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - datetime.timedelta(days=days)
    
    # Get security events
    security_events = SecurityEvent.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).values('event_type', 'severity').annotate(
        count=Count('id')
    )
    
    # Get audit events
    audit_events = AuditEvent.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).values('event_type', 'severity').annotate(
        count=Count('id')
    )
    
    # Get PII detection trends
    pii_trend = DailyMetricAggregate.objects.filter(
        date__gte=start_date.date(),
        date__lte=end_date.date()
    ).values('date', 'pii_detection_count')
    
    return JsonResponse({
        'security_events': list(security_events),
        'audit_events': list(audit_events),
        'pii_trend': list(pii_trend),
        'period': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'days': days
        }
    })