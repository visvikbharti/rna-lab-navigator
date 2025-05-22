"""
Data aggregation utilities for analytics dashboard.
Processes raw metrics and events into aggregated statistics for efficient display.
"""

from django.db.models import Avg, Count, Max, F, Q, Sum
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import json
import re

from .models import (
    SystemMetric, 
    UserActivityLog, 
    AuditEvent, 
    DailyMetricAggregate,
    QueryTypeAggregate,
    SecurityEvent
)


class MetricsAggregator:
    """
    Aggregates raw metrics and events into summary statistics.
    Used for generating dashboard data and scheduled reports.
    """
    
    @classmethod
    def aggregate_daily_metrics(cls, date=None):
        """
        Aggregate metrics for a specific day.
        If date is None, aggregates for the previous day.
        """
        if date is None:
            # Default to yesterday
            date = (timezone.now() - datetime.timedelta(days=1)).date()
        
        # Define date range for the day
        start_datetime = datetime.datetime.combine(date, datetime.time.min)
        end_datetime = datetime.datetime.combine(date, datetime.time.max)
        
        # Get or create the daily aggregate object
        daily_agg, created = DailyMetricAggregate.objects.get_or_create(date=date)
        
        # Count total queries
        query_logs = UserActivityLog.objects.filter(
            activity_type='query',
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        )
        daily_agg.total_queries = query_logs.count()
        
        # Count unique users
        daily_agg.unique_users = UserActivityLog.objects.filter(
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        ).values('user').distinct().count()
        
        # Calculate average response time
        response_time_metrics = SystemMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        )
        if response_time_metrics.exists():
            daily_agg.avg_response_time = response_time_metrics.aggregate(avg=Avg('value'))['avg']
            daily_agg.max_response_time = response_time_metrics.aggregate(max=Max('value'))['max']
        
        # Count document uploads
        daily_agg.document_uploads = UserActivityLog.objects.filter(
            activity_type='document_upload',
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        ).count()
        
        # Count document views
        daily_agg.document_views = UserActivityLog.objects.filter(
            activity_type='document_view',
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        ).count()
        
        # Count errors
        daily_agg.error_count = UserActivityLog.objects.filter(
            status='failure',
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        ).count()
        
        # Count PII detections
        daily_agg.pii_detection_count = AuditEvent.objects.filter(
            event_type='pii_detection',
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        ).count()
        
        # Additional metrics
        daily_agg.metadata = cls._calculate_additional_metrics(start_datetime, end_datetime)
        
        # Save the updated aggregate
        daily_agg.save()
        
        return daily_agg
    
    @classmethod
    def _calculate_additional_metrics(cls, start_datetime, end_datetime):
        """Calculate additional metrics for the metadata field"""
        metadata = {}
        
        # Add system component performance
        system_metrics = {}
        for metric_type in ['cpu_usage', 'memory_usage', 'vector_search_time', 'llm_generation_time']:
            metrics = SystemMetric.objects.filter(
                metric_type=metric_type,
                timestamp__gte=start_datetime,
                timestamp__lte=end_datetime
            )
            
            if metrics.exists():
                system_metrics[metric_type] = {
                    'avg': metrics.aggregate(avg=Avg('value'))['avg'],
                    'max': metrics.aggregate(max=Max('value'))['max'],
                }
        
        if system_metrics:
            metadata['system_metrics'] = system_metrics
        
        # Security events summary
        security_events = AuditEvent.objects.filter(
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        ).values('event_type').annotate(count=Count('id'))
        
        if security_events:
            metadata['security_events'] = {
                item['event_type']: item['count'] for item in security_events
            }
        
        # User activity patterns
        user_activity = UserActivityLog.objects.filter(
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        ).values('activity_type').annotate(count=Count('id'))
        
        if user_activity:
            metadata['user_activity'] = {
                item['activity_type']: item['count'] for item in user_activity
            }
        
        return metadata
    
    @classmethod
    def aggregate_query_types(cls, date=None, num_days=1):
        """
        Analyze and aggregate query types/categories.
        Groups queries into categories based on content analysis.
        """
        if date is None:
            date = (timezone.now() - datetime.timedelta(days=1)).date()
        
        # Get date range
        start_datetime = datetime.datetime.combine(date - datetime.timedelta(days=num_days-1), datetime.time.min)
        end_datetime = datetime.datetime.combine(date, datetime.time.max)
        
        # Get all query activities with text
        query_logs = UserActivityLog.objects.filter(
            activity_type='query',
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime
        ).exclude(metadata__query_text__isnull=True)
        
        # Define category patterns
        category_patterns = {
            'protocol': r'protocol|procedure|method|how to|steps|recipe',
            'troubleshooting': r'error|issue|problem|fail|trouble|not working|debug',
            'reagent': r'reagent|chemical|solution|buffer|media|enzyme',
            'equipment': r'machine|device|equipment|instrument|apparatus',
            'theory': r'theory|concept|principle|mechanism|explain',
            'reference': r'paper|publication|journal|reference|cite|author',
            'calculation': r'calculate|compute|equation|formula|concentration|dilution',
            'safety': r'safety|hazard|danger|precaution|protection',
            'technique': r'technique|assay|analysis|test|measurement',
        }
        
        # Initialize counters
        category_data = {cat: {'count': 0, 'examples': []} for cat in category_patterns.keys()}
        category_data['other'] = {'count': 0, 'examples': []}
        
        # Analyze each query
        for log in query_logs:
            query_text = log.metadata.get('query_text', '')
            if not query_text:
                continue
            
            # Check each category pattern
            categorized = False
            for category, pattern in category_patterns.items():
                if re.search(pattern, query_text, re.IGNORECASE):
                    category_data[category]['count'] += 1
                    if len(category_data[category]['examples']) < 5:  # Limit examples
                        category_data[category]['examples'].append(query_text[:100])
                    categorized = True
                    break
            
            # If no category matched, add to 'other'
            if not categorized:
                category_data['other']['count'] += 1
                if len(category_data['other']['examples']) < 5:
                    category_data['other']['examples'].append(query_text[:100])
        
        # Save aggregated data
        for category, data in category_data.items():
            if data['count'] > 0:
                QueryTypeAggregate.objects.update_or_create(
                    category=category,
                    date=date,
                    defaults={
                        'count': data['count'],
                        'examples': data['examples']
                    }
                )
        
        return category_data
    
    @classmethod
    def get_dashboard_summary(cls, days=7):
        """
        Generate a summary of metrics for the dashboard.
        Returns aggregated data for the specified number of days.
        """
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days-1)
        
        # Get daily aggregates for the period
        daily_aggregates = DailyMetricAggregate.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Calculate summary metrics
        summary = {
            'period_start': start_date,
            'period_end': end_date,
            'total_queries': sum(agg.total_queries for agg in daily_aggregates),
            'total_unique_users': User.objects.filter(
                activity_logs__timestamp__gte=datetime.datetime.combine(start_date, datetime.time.min),
                activity_logs__timestamp__lte=datetime.datetime.combine(end_date, datetime.time.max)
            ).distinct().count(),
            'avg_response_time': daily_aggregates.aggregate(avg=Avg('avg_response_time'))['avg'],
            'document_uploads': sum(agg.document_uploads for agg in daily_aggregates),
            'error_rate': sum(agg.error_count for agg in daily_aggregates) / 
                          (sum(agg.total_queries for agg in daily_aggregates) or 1) * 100,
            'daily_trends': [
                {
                    'date': agg.date,
                    'queries': agg.total_queries,
                    'users': agg.unique_users,
                    'response_time': agg.avg_response_time,
                    'errors': agg.error_count,
                }
                for agg in daily_aggregates
            ],
        }
        
        # Get query type distribution
        query_types = QueryTypeAggregate.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).values('category').annotate(total=Sum('count')).order_by('-total')
        
        summary['query_distribution'] = {
            item['category']: item['total'] for item in query_types
        }
        
        # Get security event summary
        security_events = AuditEvent.objects.filter(
            timestamp__gte=datetime.datetime.combine(start_date, datetime.time.min),
            timestamp__lte=datetime.datetime.combine(end_date, datetime.time.max)
        ).values('event_type', 'severity').annotate(count=Count('id'))
        
        summary['security_events'] = {
            'by_type': {item['event_type']: item['count'] for item in security_events},
            'by_severity': {}
        }
        
        # Group security events by severity
        for severity in ['info', 'warning', 'error', 'critical']:
            count = sum(item['count'] for item in security_events if item['severity'] == severity)
            if count > 0:
                summary['security_events']['by_severity'][severity] = count
        
        return summary