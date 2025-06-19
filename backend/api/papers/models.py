"""
Models for paper monitoring and tracking
"""
from django.db import models
import uuid
from django.utils import timezone


class MonitoredPaper(models.Model):
    """Track papers discovered through automated monitoring."""
    
    RELEVANCE_CHOICES = [
        ('urgent', 'Urgent - Immediate attention'),
        ('relevant', 'Relevant - Weekly digest'),
        ('monitoring', 'Monitoring - Low priority'),
        ('archived', 'Archived - Processed')
    ]
    
    SOURCE_CHOICES = [
        ('biorxiv', 'bioRxiv'),
        ('research_square', 'Research Square'),
        ('pubmed', 'PubMed'),
        ('arxiv', 'arXiv'),
        ('manual', 'Manual Entry')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    authors = models.TextField()
    abstract = models.TextField()
    doi = models.CharField(max_length=200, unique=True, null=True, blank=True)
    url = models.URLField()
    
    # Metadata
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    category = models.CharField(max_length=100)  # e.g., 'molecular_biology'
    published_date = models.DateTimeField()
    discovered_date = models.DateTimeField(default=timezone.now)
    
    # Relevance scoring
    relevance_score = models.FloatField(default=0)
    relevance_category = models.CharField(max_length=20, choices=RELEVANCE_CHOICES)
    relevance_reasons = models.JSONField(default=list)  # List of reasons why it's relevant
    
    # AI-generated content
    smart_summary = models.TextField(blank=True)
    experiment_suggestions = models.TextField(blank=True)
    key_findings = models.JSONField(default=list)
    
    # Tracking
    is_ingested = models.BooleanField(default=False)  # Has been added to main document store
    is_notified = models.BooleanField(default=False)  # Has been sent in notifications
    clicked_count = models.IntegerField(default=0)  # Track engagement
    
    # Lab member interactions
    flagged_by = models.JSONField(default=list)  # List of user IDs who flagged this
    notes = models.TextField(blank=True)  # Internal notes
    
    class Meta:
        ordering = ['-relevance_score', '-published_date']
        indexes = [
            models.Index(fields=['relevance_category', 'is_notified']),
            models.Index(fields=['published_date']),
            models.Index(fields=['doi']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.relevance_category})"
    
    def increment_click(self):
        """Track when someone views this paper."""
        self.clicked_count += 1
        self.save(update_fields=['clicked_count'])


class PaperNotification(models.Model):
    """Track notifications sent about papers."""
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('slack', 'Slack'),
        ('whatsapp', 'WhatsApp'),
        ('web', 'Web Dashboard')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paper = models.ForeignKey(MonitoredPaper, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    sent_at = models.DateTimeField(default=timezone.now)
    recipient = models.CharField(max_length=200)  # Email, phone, or user ID
    is_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.paper.title} -> {self.recipient} via {self.channel}"


class PaperKeyword(models.Model):
    """Lab-specific keywords for paper monitoring."""
    
    PRIORITY_CHOICES = [
        ('urgent', 'Urgent - Triggers immediate alerts'),
        ('high', 'High - Important for research'),
        ('medium', 'Medium - General interest'),
        ('low', 'Low - Background monitoring')
    ]
    
    keyword = models.CharField(max_length=100, unique=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    score_boost = models.IntegerField(default=10)  # How much to boost relevance score
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-priority', 'keyword']
    
    def __str__(self):
        return f"{self.keyword} ({self.priority})"