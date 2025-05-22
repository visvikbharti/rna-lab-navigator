"""
Serializers for security audit and monitoring.
Provides serialization for security models and related data.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from api.analytics.models import SecurityEvent, AuditEvent
from .models import (
    BlockedIP,
    SecurityConfiguration,
    SecurityScan,
    SecurityIncident,
    WAFAlert
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']


class SecurityEventSerializer(serializers.ModelSerializer):
    """Serializer for SecurityEvent model."""
    user = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = SecurityEvent
        fields = '__all__'


class AuditEventSerializer(serializers.ModelSerializer):
    """Serializer for AuditEvent model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditEvent
        fields = '__all__'


class BlockedIPSerializer(serializers.ModelSerializer):
    """Serializer for BlockedIP model."""
    blocked_by = UserSerializer(read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = BlockedIP
        fields = '__all__'
    
    def get_status(self, obj):
        """Get the current block status."""
        import django.utils.timezone as timezone
        now = timezone.now()
        
        if obj.is_permanent:
            return "permanent"
        elif obj.blocked_until and obj.blocked_until > now:
            return "active"
        else:
            return "expired"


class SecurityConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for SecurityConfiguration model."""
    changed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = SecurityConfiguration
        fields = '__all__'


class SecurityScanSerializer(serializers.ModelSerializer):
    """Serializer for SecurityScan model."""
    initiated_by = UserSerializer(read_only=True)
    total_findings = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityScan
        fields = '__all__'
    
    def get_total_findings(self, obj):
        """Get the total number of findings."""
        return obj.high_severity_findings + obj.medium_severity_findings + obj.low_severity_findings


class SecurityIncidentSerializer(serializers.ModelSerializer):
    """Serializer for SecurityIncident model."""
    reported_by = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = SecurityIncident
        fields = '__all__'


class WAFAlertSerializer(serializers.ModelSerializer):
    """Serializer for WAFAlert model."""
    user = UserSerializer(read_only=True)
    related_security_event = SecurityEventSerializer(read_only=True)
    
    class Meta:
        model = WAFAlert
        fields = '__all__'


class SecurityDashboardSummarySerializer(serializers.Serializer):
    """Serializer for security dashboard summary."""
    metrics = serializers.DictField(child=serializers.IntegerField())
    top_attack_vectors = serializers.ListField(child=serializers.DictField())
    top_targeted_endpoints = serializers.ListField(child=serializers.DictField())
    recent_incidents = SecurityIncidentSerializer(many=True)
    daily_events = serializers.ListField(child=serializers.DictField())
    waf_by_attack_type = serializers.ListField(child=serializers.DictField())
    events_by_type = serializers.ListField(child=serializers.DictField())


class SecurityHealthCheckSerializer(serializers.Serializer):
    """Serializer for security health check."""
    status = serializers.CharField()
    findings = serializers.ListField(child=serializers.DictField())
    last_checked = serializers.DateTimeField()
    checks_performed = serializers.IntegerField()
    critical_issues = serializers.IntegerField()
    high_issues = serializers.IntegerField()
    medium_issues = serializers.IntegerField()