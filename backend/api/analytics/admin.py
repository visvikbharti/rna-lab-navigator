"""
Admin views for the analytics models.
Provides visualizations and filters for analytics data in the Django admin.
"""

from django.contrib import admin
from django.db.models import Count, Avg
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
import datetime
import json

from .models import (
    SystemMetric,
    AuditEvent,
    UserActivityLog,
    DailyMetricAggregate,
    QueryTypeAggregate,
    SecurityEvent,
    SystemStatusLog
)


class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ('metric_type', 'value', 'unit', 'timestamp')
    list_filter = ('metric_type', 'timestamp')
    search_fields = ('metric_type', 'metadata')
    date_hierarchy = 'timestamp'


class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'severity', 'timestamp', 'description')
    list_filter = ('event_type', 'severity', 'timestamp')
    search_fields = ('description', 'user__username', 'ip_address')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('user',)


class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'user', 'timestamp', 'ip_address', 'status')
    list_filter = ('activity_type', 'timestamp', 'status')
    search_fields = ('user__username', 'session_id', 'ip_address', 'resource_id')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('user',)


class DailyMetricAggregateAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_queries', 'unique_users', 'avg_response_time', 'error_count')
    list_filter = ('date',)
    date_hierarchy = 'date'
    
    change_list_template = 'admin/analytics/metrics_dashboard.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('metrics-data/', self.admin_site.admin_view(self.metrics_data_view), name='analytics_metrics_data'),
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='analytics_dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """View for the analytics dashboard"""
        context = {
            **self.admin_site.each_context(request),
            'title': 'Analytics Dashboard',
        }
        return TemplateResponse(request, 'admin/analytics/dashboard.html', context)
    
    def metrics_data_view(self, request):
        """API endpoint for dashboard charts"""
        days = int(request.GET.get('days', 30))
        
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days)
        
        daily_metrics = DailyMetricAggregate.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Prepare time series data
        time_series = {
            'dates': [m.date.strftime('%Y-%m-%d') for m in daily_metrics],
            'queries': [m.total_queries for m in daily_metrics],
            'users': [m.unique_users for m in daily_metrics],
            'response_times': [m.avg_response_time or 0 for m in daily_metrics],
            'errors': [m.error_count for m in daily_metrics],
        }
        
        # Get query type distribution
        query_types = QueryTypeAggregate.objects.filter(
            date__gte=start_date
        ).values('category').annotate(total=Count('category'))
        
        query_distribution = {
            'categories': [qt['category'] for qt in query_types],
            'counts': [qt['total'] for qt in query_types],
        }
        
        # Get security event summary
        security_events = AuditEvent.objects.filter(
            timestamp__gte=datetime.datetime.combine(start_date, datetime.time.min)
        ).values('severity').annotate(count=Count('id'))
        
        security_summary = {
            'labels': [se['severity'] for se in security_events],
            'counts': [se['count'] for se in security_events],
        }
        
        return JsonResponse({
            'time_series': time_series,
            'query_distribution': query_distribution,
            'security_summary': security_summary,
        })


class QueryTypeAggregateAdmin(admin.ModelAdmin):
    list_display = ('category', 'date', 'count', 'avg_confidence')
    list_filter = ('category', 'date')
    search_fields = ('category',)
    date_hierarchy = 'date'


class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'timestamp', 'severity', 'user', 'is_resolved', 'resolution_status')
    list_filter = ('event_type', 'severity', 'is_resolved', 'timestamp')
    search_fields = ('description', 'user__username', 'ip_address')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('user', 'resolved_by')
    
    def resolution_status(self, obj):
        if obj.is_resolved:
            return format_html(
                '<span style="color: green;">Resolved by {} on {}</span>',
                obj.resolved_by.username if obj.resolved_by else 'Unknown',
                obj.resolved_at.strftime('%Y-%m-%d %H:%M') if obj.resolved_at else 'Unknown'
            )
        return format_html('<span style="color: red;">Unresolved</span>')
    resolution_status.short_description = 'Resolution'


class SystemStatusLogAdmin(admin.ModelAdmin):
    list_display = ('component', 'status', 'timestamp', 'message')
    list_filter = ('component', 'status', 'timestamp')
    search_fields = ('message', 'component')
    date_hierarchy = 'timestamp'
    
    def status_display(self, obj):
        status_colors = {
            'healthy': 'green',
            'degraded': 'orange',
            'down': 'red',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    status_display.short_description = 'Status'


# Register models with the admin site
admin.site.register(SystemMetric, SystemMetricAdmin)
admin.site.register(AuditEvent, AuditEventAdmin)
admin.site.register(UserActivityLog, UserActivityLogAdmin)
admin.site.register(DailyMetricAggregate, DailyMetricAggregateAdmin)
admin.site.register(QueryTypeAggregate, QueryTypeAggregateAdmin)
admin.site.register(SecurityEvent, SecurityEventAdmin)
admin.site.register(SystemStatusLog, SystemStatusLogAdmin)