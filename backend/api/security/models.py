"""
Models for security audit and monitoring.
Extends the analytics app with security-specific models.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from api.analytics.models import SecurityEvent


class BlockedIP(models.Model):
    """
    Model for tracking blocked IP addresses.
    IPs can be blocked manually or automatically by security systems.
    """
    
    BLOCK_REASONS = (
        ('rate_limit', 'Rate Limit Exceeded'),
        ('suspicious', 'Suspicious Activity'),
        ('attack', 'Attack Detected'),
        ('manual', 'Manually Blocked'),
        ('brute_force', 'Brute Force Attempt'),
    )
    
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=50, choices=BLOCK_REASONS)
    blocked_at = models.DateTimeField(default=timezone.now)
    blocked_until = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    blocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='blocked_ips')
    is_permanent = models.BooleanField(default=False)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-blocked_at']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['reason']),
            models.Index(fields=['blocked_at']),
            models.Index(fields=['is_permanent']),
        ]
    
    def __str__(self):
        duration = "permanently" if self.is_permanent else f"until {self.blocked_until}"
        return f"{self.ip_address} blocked {duration} for {self.reason}"
    
    @classmethod
    def is_blocked(cls, ip_address):
        """Check if an IP is currently blocked"""
        now = timezone.now()
        return cls.objects.filter(
            ip_address=ip_address,
        ).filter(
            models.Q(is_permanent=True) |
            models.Q(blocked_until__gt=now)
        ).exists()


class SecurityConfiguration(models.Model):
    """
    Model for tracking security configuration changes.
    Maintains history of security settings for audit purposes.
    """
    
    CONFIGURATION_TYPES = (
        ('rate_limit', 'Rate Limiting'),
        ('waf', 'Web Application Firewall'),
        ('authentication', 'Authentication'),
        ('authorization', 'Authorization'),
        ('encryption', 'Encryption'),
        ('network', 'Network Security'),
        ('headers', 'Security Headers'),
    )
    
    configuration_type = models.CharField(max_length=50, choices=CONFIGURATION_TYPES)
    key = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField()
    changed_at = models.DateTimeField(default=timezone.now)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['configuration_type']),
            models.Index(fields=['key']),
            models.Index(fields=['changed_at']),
            models.Index(fields=['changed_by']),
        ]
    
    def __str__(self):
        return f"{self.configuration_type}.{self.key} changed on {self.changed_at.strftime('%Y-%m-%d %H:%M')}"


class SecurityScan(models.Model):
    """
    Model for tracking security scans.
    Records vulnerability scans, penetration tests, and audits.
    """
    
    SCAN_TYPES = (
        ('vulnerability', 'Vulnerability Scan'),
        ('penetration', 'Penetration Test'),
        ('compliance', 'Compliance Audit'),
        ('code', 'Code Security Review'),
        ('config', 'Configuration Review'),
    )
    
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    scan_type = models.CharField(max_length=50, choices=SCAN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tool = models.CharField(max_length=100, blank=True)
    summary = models.TextField(blank=True)
    high_severity_findings = models.PositiveSmallIntegerField(default=0)
    medium_severity_findings = models.PositiveSmallIntegerField(default=0)
    low_severity_findings = models.PositiveSmallIntegerField(default=0)
    results = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['scan_type']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"{self.scan_type} {self.status} on {self.started_at.strftime('%Y-%m-%d')}"


class SecurityIncident(models.Model):
    """
    Model for tracking security incidents.
    Records breaches, attacks, and other security incidents.
    """
    
    INCIDENT_TYPES = (
        ('breach', 'Data Breach'),
        ('attack', 'Attack'),
        ('misconfiguration', 'Security Misconfiguration'),
        ('insider', 'Insider Threat'),
        ('compliance', 'Compliance Violation'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('detected', 'Detected'),
        ('investigating', 'Under Investigation'),
        ('contained', 'Contained'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    SEVERITY_LEVELS = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    detected_at = models.DateTimeField(default=timezone.now)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_incidents')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_incidents')
    affected_systems = models.TextField(blank=True)
    description = models.TextField()
    response_actions = models.TextField(blank=True)
    root_cause_analysis = models.TextField(blank=True)
    prevention_measures = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['incident_type']),
            models.Index(fields=['status']),
            models.Index(fields=['severity']),
            models.Index(fields=['detected_at']),
        ]
    
    def __str__(self):
        return f"{self.severity} {self.incident_type} incident ({self.status}) on {self.detected_at.strftime('%Y-%m-%d')}"


class WAFAlert(models.Model):
    """
    Model for tracking WAF alerts.
    Records details of potential attacks caught by the WAF.
    """
    
    ATTACK_TYPES = (
        ('sql_injection', 'SQL Injection'),
        ('xss', 'Cross-Site Scripting'),
        ('csrf', 'Cross-Site Request Forgery'),
        ('lfi', 'Local File Inclusion'),
        ('command_injection', 'Command Injection'),
        ('path_traversal', 'Path Traversal'),
        ('ip_reputation', 'IP Reputation'),
        ('other', 'Other'),
    )
    
    SEVERITY_LEVELS = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    
    ACTION_TAKEN = (
        ('block', 'Blocked'),
        ('alert', 'Alert Only'),
        ('challenge', 'Challenged User'),
        ('log', 'Logged Only'),
    )
    
    attack_type = models.CharField(max_length=50, choices=ATTACK_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    request_path = models.CharField(max_length=255)
    request_method = models.CharField(max_length=10)
    matched_pattern = models.CharField(max_length=255, blank=True)
    action_taken = models.CharField(max_length=20, choices=ACTION_TAKEN)
    request_details = models.JSONField(default=dict, blank=True)
    is_false_positive = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    # Link to security events for unified views
    related_security_event = models.ForeignKey(SecurityEvent, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['attack_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['action_taken']),
            models.Index(fields=['is_false_positive']),
        ]
    
    def __str__(self):
        return f"{self.attack_type} ({self.severity}) - {self.action_taken} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"