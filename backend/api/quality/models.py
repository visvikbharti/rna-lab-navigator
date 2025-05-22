"""
Models for the answer quality improvement pipeline.

This includes models for tracking quality analyses, improvements,
enhanced prompts, and retrieval configurations.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

from ..models import QueryHistory
from ..feedback.models import EnhancedFeedback, FeedbackTheme


class QualityAnalysis(models.Model):
    """
    Stores analysis of feedback patterns to identify common issues
    and areas for improvement in answer quality.
    """

    ANALYSIS_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    ANALYSIS_TYPE_CHOICES = (
        ('general', 'General Quality Analysis'),
        ('topic_specific', 'Topic-Specific Analysis'),
        ('prompt_focused', 'Prompt Optimization Analysis'),
        ('retrieval_focused', 'Retrieval Optimization Analysis'),
        ('citation_focused', 'Citation Quality Analysis'),
    )

    # Basic fields
    analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPE_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=ANALYSIS_STATUS_CHOICES, default='pending')
    
    # Timing fields
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Analysis parameters
    date_range_start = models.DateTimeField()
    date_range_end = models.DateTimeField()
    feedback_count = models.PositiveIntegerField(default=0)
    feedback_filter = models.JSONField(blank=True, null=True, 
                                       help_text="JSON filters applied to select feedback for analysis")
    
    # Analysis results
    identified_issues = models.JSONField(blank=True, null=True)
    issue_frequencies = models.JSONField(blank=True, null=True)
    topic_clusters = models.JSONField(blank=True, null=True)
    difficulty_assessment = models.JSONField(blank=True, null=True)
    
    # Summary and recommendations
    summary = models.TextField(blank=True)
    primary_issues = models.JSONField(blank=True, null=True)
    quality_score = models.FloatField(null=True, blank=True)
    
    # Relations
    related_themes = models.ManyToManyField(
        FeedbackTheme, 
        blank=True,
        related_name='quality_analyses'
    )
    
    class Meta:
        verbose_name = "Quality Analysis"
        verbose_name_plural = "Quality Analyses"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def start_analysis(self):
        """Mark analysis as started."""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def complete_analysis(self, results, summary):
        """
        Mark analysis as completed with results.
        
        Args:
            results (dict): Analysis results
            summary (str): Summary of the analysis
        """
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.identified_issues = results.get('identified_issues')
        self.issue_frequencies = results.get('issue_frequencies')
        self.topic_clusters = results.get('topic_clusters')
        self.difficulty_assessment = results.get('difficulty_assessment')
        self.primary_issues = results.get('primary_issues')
        self.quality_score = results.get('quality_score')
        self.summary = summary
        self.feedback_count = results.get('feedback_count', 0)
        self.save()


class QualityImprovement(models.Model):
    """
    Tracks quality improvement recommendations and their implementation.
    """
    
    IMPROVEMENT_STATUS_CHOICES = (
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
        ('reverted', 'Reverted'),
    )
    
    IMPROVEMENT_TYPE_CHOICES = (
        ('prompt', 'Prompt Improvement'),
        ('retrieval', 'Retrieval Configuration'),
        ('citation', 'Citation Enhancement'),
        ('model', 'Model Configuration'),
        ('chunking', 'Chunking Strategy'),
        ('other', 'Other Improvement'),
    )
    
    PRIORITY_CHOICES = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    
    # Basic fields
    improvement_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    improvement_type = models.CharField(max_length=50, choices=IMPROVEMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=IMPROVEMENT_STATUS_CHOICES, default='proposed')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Timing fields
    created_at = models.DateTimeField(default=timezone.now)
    approved_at = models.DateTimeField(null=True, blank=True)
    implemented_at = models.DateTimeField(null=True, blank=True)
    
    # Improvement details
    implementation_details = models.JSONField(blank=True, null=True)
    expected_impact = models.TextField(blank=True)
    implementation_effort = models.CharField(max_length=50, blank=True)
    impact_score = models.FloatField(null=True, blank=True, 
                                     help_text="Estimated impact score (0-1)")
    
    # Results tracking
    actual_impact = models.TextField(blank=True)
    impact_metrics = models.JSONField(blank=True, null=True)
    before_metrics = models.JSONField(blank=True, null=True)
    after_metrics = models.JSONField(blank=True, null=True)
    
    # Relations
    source_analysis = models.ForeignKey(
        QualityAnalysis,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='improvement_recommendations'
    )
    target_issues = models.JSONField(blank=True, null=True)
    related_feedback = models.ManyToManyField(
        EnhancedFeedback,
        blank=True,
        related_name='target_improvements'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_improvements'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_improvements'
    )
    
    class Meta:
        verbose_name = "Quality Improvement"
        verbose_name_plural = "Quality Improvements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def approve(self, user=None):
        """
        Approve the improvement for implementation.
        
        Args:
            user: The user approving the improvement (optional)
        """
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.approved_by = user
        self.save()
    
    def implement(self, implementation_details=None):
        """
        Mark the improvement as implemented.
        
        Args:
            implementation_details: Details about the implementation (optional)
        """
        self.status = 'implemented'
        self.implemented_at = timezone.now()
        if implementation_details:
            self.implementation_details = implementation_details
        self.save()
    
    def record_impact(self, actual_impact, metrics=None):
        """
        Record the actual impact of the improvement.
        
        Args:
            actual_impact (str): Description of the actual impact
            metrics (dict): Metrics measuring the impact
        """
        self.actual_impact = actual_impact
        if metrics:
            self.after_metrics = metrics
        self.save()


class ImprovedPrompt(models.Model):
    """
    Manages enhanced prompts based on feedback and quality improvements.
    """
    
    PROMPT_TYPE_CHOICES = (
        ('system', 'System Prompt'),
        ('answer_generation', 'Answer Generation Prompt'),
        ('citation', 'Citation Prompt'),
        ('specialized', 'Specialized Topic Prompt'),
    )
    
    PROMPT_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('testing', 'In Testing'),
    )
    
    # Basic fields
    prompt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    prompt_type = models.CharField(max_length=50, choices=PROMPT_TYPE_CHOICES)
    prompt_text = models.TextField()
    status = models.CharField(max_length=20, choices=PROMPT_STATUS_CHOICES, default='draft')
    
    # Timing and versioning
    created_at = models.DateTimeField(default=timezone.now)
    activated_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    
    # Related fields
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions'
    )
    source_improvement = models.ForeignKey(
        QualityImprovement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resulting_prompts'
    )
    
    # Performance metrics
    performance_metrics = models.JSONField(blank=True, null=True)
    topic_applicability = models.JSONField(blank=True, null=True, 
                                           help_text="Topics this prompt is optimized for")
    usage_count = models.PositiveIntegerField(default=0)
    avg_quality_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Improved Prompt"
        verbose_name_plural = "Improved Prompts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_status_display()})"
    
    def activate(self):
        """Activate this prompt for use in the system."""
        # First archive any active prompts of the same type
        ImprovedPrompt.objects.filter(
            prompt_type=self.prompt_type,
            status='active'
        ).update(status='archived')
        
        # Then activate this prompt
        self.status = 'active'
        self.activated_at = timezone.now()
        self.save()
    
    def create_new_version(self, prompt_text, description=None):
        """
        Create a new version of this prompt.
        
        Args:
            prompt_text (str): Text for the new prompt version
            description (str): Description of changes (optional)
            
        Returns:
            ImprovedPrompt: The new prompt version
        """
        return ImprovedPrompt.objects.create(
            name=self.name,
            description=description or f"New version of {self.name}",
            prompt_type=self.prompt_type,
            prompt_text=prompt_text,
            status='draft',
            version=self.version + 1,
            previous_version=self,
            source_improvement=self.source_improvement,
            topic_applicability=self.topic_applicability
        )
    
    def update_metrics(self, metrics):
        """
        Update the performance metrics for this prompt.
        
        Args:
            metrics (dict): New performance metrics
        """
        self.performance_metrics = metrics
        if 'quality_score' in metrics:
            self.avg_quality_score = metrics['quality_score']
        self.save()


class RetrievalConfiguration(models.Model):
    """
    Stores retrieval parameter configurations optimized based on feedback.
    """
    
    CONFIG_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('testing', 'In Testing'),
    )
    
    # Basic fields
    config_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parameters = models.JSONField()
    status = models.CharField(max_length=20, choices=CONFIG_STATUS_CHOICES, default='draft')
    
    # Timing and versioning
    created_at = models.DateTimeField(default=timezone.now)
    activated_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    
    # Related fields
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions'
    )
    source_improvement = models.ForeignKey(
        QualityImprovement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resulting_configs'
    )
    
    # Performance metrics
    performance_metrics = models.JSONField(blank=True, null=True)
    topic_applicability = models.JSONField(blank=True, null=True, 
                                           help_text="Topics this configuration is optimized for")
    usage_count = models.PositiveIntegerField(default=0)
    avg_quality_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Retrieval Configuration"
        verbose_name_plural = "Retrieval Configurations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_status_display()})"
    
    def activate(self):
        """Activate this configuration for use in the system."""
        # First archive any active configurations
        RetrievalConfiguration.objects.filter(
            status='active'
        ).update(status='archived')
        
        # Then activate this configuration
        self.status = 'active'
        self.activated_at = timezone.now()
        self.save()
    
    def create_new_version(self, parameters, description=None):
        """
        Create a new version of this configuration.
        
        Args:
            parameters (dict): Parameters for the new configuration
            description (str): Description of changes (optional)
            
        Returns:
            RetrievalConfiguration: The new configuration version
        """
        return RetrievalConfiguration.objects.create(
            name=self.name,
            description=description or f"New version of {self.name}",
            parameters=parameters,
            status='draft',
            version=self.version + 1,
            previous_version=self,
            source_improvement=self.source_improvement,
            topic_applicability=self.topic_applicability
        )
    
    def update_metrics(self, metrics):
        """
        Update the performance metrics for this configuration.
        
        Args:
            metrics (dict): New performance metrics
        """
        self.performance_metrics = metrics
        if 'quality_score' in metrics:
            self.avg_quality_score = metrics['quality_score']
        self.save()