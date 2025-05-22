"""
Models for analytics and audit dashboard.
Stores metrics, events, and aggregated statistics for the RNA Lab Navigator.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SystemMetric(models.Model):
    """
    Model for storing system performance metrics.
    Captures point-in-time measurements of system performance.
    """
    
    METRIC_TYPES = (
        ('response_time', 'Response Time'),
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('db_query_time', 'Database Query Time'),
        ('vector_search_time', 'Vector Search Time'),
        ('llm_generation_time', 'LLM Generation Time'),
        ('embedding_generation_time', 'Embedding Generation Time'),
        ('cache_hit_rate', 'Cache Hit Rate'),
        ('error_rate', 'Error Rate'),
    )
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    value = models.FloatField()
    unit = models.CharField(max_length=20, default="ms")
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['metric_type']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_type}: {self.value} {self.unit} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class AuditEvent(models.Model):
    """
    Model for storing audit events.
    Captures security-relevant events for auditing and compliance.
    """
    
    EVENT_TYPES = (
        ('authentication', 'Authentication'),
        ('authorization', 'Authorization'),
        ('data_access', 'Data Access'),
        ('data_modification', 'Data Modification'),
        ('security_setting', 'Security Setting Change'),
        ('system_operation', 'System Operation'),
        ('user_management', 'User Management'),
        ('pii_detection', 'PII Detection'),
    )
    
    SEVERITY_LEVELS = (
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    )
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_events')
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info')
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['severity']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{self.event_type} by {user_str} - {self.severity} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class UserActivityLog(models.Model):
    """
    Model for logging user activity.
    Tracks user interactions with the system.
    """
    
    ACTIVITY_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('query', 'Query'),
        ('document_view', 'Document View'),
        ('document_upload', 'Document Upload'),
        ('feedback', 'Feedback'),
        ('setting_change', 'Setting Change'),
        ('admin_action', 'Admin Action'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_id = models.CharField(max_length=128, null=True, blank=True)
    resource_id = models.CharField(max_length=128, null=True, blank=True)
    resource_type = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, default='success')
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['session_id']),
            models.Index(fields=['resource_type']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{self.activity_type} by {user_str} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class DailyMetricAggregate(models.Model):
    """
    Model for storing daily aggregated metrics.
    Used for efficient dashboard rendering and trend analysis.
    """
    
    date = models.DateField(unique=True)
    total_queries = models.PositiveIntegerField(default=0)
    unique_users = models.PositiveIntegerField(default=0)
    avg_response_time = models.FloatField(null=True, blank=True)
    avg_confidence_score = models.FloatField(null=True, blank=True)
    cache_hit_rate = models.FloatField(null=True, blank=True)
    error_count = models.PositiveIntegerField(default=0)
    pii_detection_count = models.PositiveIntegerField(default=0)
    document_views = models.PositiveIntegerField(default=0)
    document_uploads = models.PositiveIntegerField(default=0)
    positive_feedback_count = models.PositiveIntegerField(default=0)
    negative_feedback_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.date.strftime('%Y-%m-%d')}"


class QueryTypeAggregate(models.Model):
    """
    Model for aggregating query types and categories.
    Helps analyze what types of questions users are asking.
    """
    
    category = models.CharField(max_length=50)
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)
    avg_confidence = models.FloatField(null=True, blank=True)
    examples = models.JSONField(default=list, blank=True)
    
    class Meta:
        unique_together = ['category', 'date']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['date']),
        ]
        ordering = ['-date', 'category']
    
    def __str__(self):
        return f"{self.category} queries for {self.date.strftime('%Y-%m-%d')}: {self.count}"


class SecurityEvent(models.Model):
    """
    Model for storing security-specific events.
    Provides detailed tracking of security-related activities.
    """
    
    EVENT_TYPES = (
        ('login_failure', 'Login Failure'),
        ('access_denied', 'Access Denied'),
        ('pii_detected', 'PII Detected'),
        ('security_scan', 'Security Scan'),
        ('configuration_change', 'Security Configuration Change'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rate_limit_warning', 'Rate Limit Warning'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('rate_limit_blocked', 'Rate Limit Blocked'),
    )
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_events')
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=AuditEvent.SEVERITY_LEVELS, default='warning')
    details = models.JSONField(default=dict, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_events')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['severity']),
            models.Index(fields=['is_resolved']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} - {self.severity} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
    
    def resolve(self, user, notes):
        """Mark event as resolved with notes"""
        self.is_resolved = True
        self.resolution_notes = notes
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()


class SystemStatusLog(models.Model):
    """
    Model for logging system status and health.
    Tracks overall system health and component status.
    """
    
    STATUS_CHOICES = (
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('down', 'Down'),
    )
    
    COMPONENT_TYPES = (
        ('api', 'API Server'),
        ('db', 'Database'),
        ('vector_db', 'Vector Database'),
        ('celery', 'Celery Worker'),
        ('redis', 'Redis Cache'),
        ('llm', 'Language Model'),
        ('embedding', 'Embedding Model'),
    )
    
    component = models.CharField(max_length=50, choices=COMPONENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['component']),
            models.Index(fields=['status']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.component}: {self.status} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"