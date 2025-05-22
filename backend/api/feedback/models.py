"""
Enhanced models for the comprehensive feedback system.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

from ..models import QueryHistory


class EnhancedFeedback(models.Model):
    """
    Enhanced feedback model that extends the basic feedback with more detailed ratings,
    categorization, and learning capabilities.
    """
    
    RATING_CHOICES = (
        ('thumbs_up', 'Thumbs Up'),
        ('thumbs_down', 'Thumbs Down'),
        ('neutral', 'Neutral'),
    )
    
    FEEDBACK_CATEGORIES = (
        ('relevance', 'Answer Relevance'),
        ('accuracy', 'Information Accuracy'),
        ('completeness', 'Answer Completeness'),
        ('clarity', 'Clarity/Readability'),
        ('citations', 'Citation Quality'),
        ('general', 'General Feedback'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('reviewed', 'Reviewed'),
        ('actioned', 'Actioned'),
        ('ignored', 'Ignored'),
    )
    
    # Base feedback fields
    query_history = models.ForeignKey(
        QueryHistory,
        on_delete=models.CASCADE,
        related_name='enhanced_feedback'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enhanced_feedback'
    )
    rating = models.CharField(max_length=15, choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    specific_issues = models.JSONField(blank=True, null=True, default=list)
    created_at = models.DateTimeField(default=timezone.now)
    
    # Enhanced fields
    category = models.CharField(
        max_length=20, 
        choices=FEEDBACK_CATEGORIES, 
        default='general'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    
    # Detailed numeric ratings (1-5 scale)
    relevance_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How relevant was the answer to the query? (1-5)"
    )
    accuracy_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How accurate was the information provided? (1-5)"
    )
    completeness_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How complete was the answer? (1-5)"
    )
    clarity_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How clear and readable was the answer? (1-5)"
    )
    citation_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How accurate and helpful were the citations? (1-5)"
    )
    
    # Learning-oriented fields
    incorrect_sections = models.JSONField(
        blank=True, 
        null=True,
        help_text="Specific sections of the answer that were incorrect"
    )
    suggested_answer = models.TextField(
        blank=True,
        help_text="User-suggested better answer or corrections"
    )
    source_quality_issues = models.JSONField(
        blank=True,
        null=True,
        help_text="Issues with the retrieved sources"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_feedback'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # System response to feedback
    system_response = models.TextField(
        blank=True,
        help_text="System response to this feedback (e.g., improvements made)"
    )
    improvement_actions = models.JSONField(
        blank=True,
        null=True,
        help_text="Actions taken to improve the system based on this feedback"
    )
    system_response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Enhanced User Feedback"
        verbose_name_plural = "Enhanced User Feedback"
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.rating} on '{self.query_history.query_text[:30]}...'"
    
    def mark_reviewed(self, user, notes=""):
        """Mark the feedback as reviewed"""
        self.status = 'reviewed'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
    
    def mark_actioned(self, response="", actions=None):
        """
        Mark the feedback as actioned with system response 
        and improvement actions
        """
        self.status = 'actioned'
        self.system_response = response
        if actions:
            self.improvement_actions = actions
        self.system_response_date = timezone.now()
        self.save()


class FeedbackCategory(models.Model):
    """
    User-configurable feedback categories and issue types.
    Allows customizing the feedback options without changing code.
    """
    
    TYPE_CHOICES = (
        ('category', 'Feedback Category'),
        ('issue', 'Specific Issue'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category for hierarchical organization"
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Feedback Category"
        verbose_name_plural = "Feedback Categories"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class FeedbackTheme(models.Model):
    """
    Aggregated feedback themes discovered through analysis.
    Used to group related feedback for prioritization and action.
    """
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('investigating', 'Investigating'),
        ('implementing', 'Implementing Solution'),
        ('resolved', 'Resolved'),
        ('wontfix', 'Won\'t Fix'),
    )
    
    PRIORITY_CHOICES = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    feedback_count = models.PositiveIntegerField(default=0, help_text="Number of feedback items in this theme")
    first_reported = models.DateTimeField(auto_now_add=True)
    last_reported = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_themes'
    )
    solution_notes = models.TextField(blank=True)
    resolution_date = models.DateTimeField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    class Meta:
        verbose_name = "Feedback Theme"
        verbose_name_plural = "Feedback Themes"
        ordering = ['-feedback_count', 'status']
    
    def __str__(self):
        return f"{self.title} ({self.feedback_count} items, {self.get_status_display()})"


class FeedbackAnalysis(models.Model):
    """
    Automated analysis of feedback for improving the system.
    Stores analysis results, recommended actions, and implementation status.
    """
    
    analysis_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date_range_start = models.DateTimeField()
    date_range_end = models.DateTimeField()
    analysis_date = models.DateTimeField(auto_now_add=True)
    total_feedback_analyzed = models.PositiveIntegerField()
    positive_feedback_count = models.PositiveIntegerField()
    negative_feedback_count = models.PositiveIntegerField()
    neutral_feedback_count = models.PositiveIntegerField()
    
    # Analysis results
    top_issues = models.JSONField(default=list)
    category_distribution = models.JSONField(default=dict)
    improvement_opportunities = models.JSONField(default=list)
    trend_analysis = models.JSONField(default=dict)
    
    # Recommendations
    recommended_actions = models.JSONField(default=list)
    priority_areas = models.JSONField(default=list)
    
    # Implementation tracking
    actions_implemented = models.JSONField(default=list)
    implementation_date = models.DateTimeField(null=True, blank=True)
    implemented_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='implemented_analyses'
    )
    effectiveness_metrics = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Feedback Analysis"
        verbose_name_plural = "Feedback Analyses"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"Analysis {self.analysis_id} - {self.analysis_date.strftime('%Y-%m-%d')}"


class FeedbackThemeMapping(models.Model):
    """
    Maps specific feedback items to themes.
    Allows one feedback item to belong to multiple themes.
    """
    
    feedback = models.ForeignKey(
        EnhancedFeedback,
        on_delete=models.CASCADE,
        related_name='theme_mappings'
    )
    theme = models.ForeignKey(
        FeedbackTheme,
        on_delete=models.CASCADE,
        related_name='feedback_mappings'
    )
    mapped_at = models.DateTimeField(auto_now_add=True)
    mapped_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    relevance_score = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How relevant this feedback is to the theme (0-1)"
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Feedback-Theme Mapping"
        verbose_name_plural = "Feedback-Theme Mappings"
        unique_together = ('feedback', 'theme')
    
    def __str__(self):
        return f"Mapping: {self.feedback} -> {self.theme}"