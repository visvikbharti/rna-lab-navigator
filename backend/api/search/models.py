"""
Models for enhanced search functionality.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

from ..models import QueryHistory


class QuerySuggestion(models.Model):
    """
    Model for storing query suggestions, including popular and trending queries.
    These can be automatically generated from query history or manually curated.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query_text = models.CharField(max_length=512, unique=True)
    category = models.CharField(max_length=50, blank=True, 
                                help_text="Optional category for grouping suggestions")
    doc_type = models.CharField(max_length=50, blank=True, 
                               help_text="Document type this query is most relevant for")
    usage_count = models.PositiveIntegerField(default=0,
                                            help_text="Number of times this query has been used")
    success_count = models.PositiveIntegerField(default=0,
                                              help_text="Number of successful answers (confidence > 0.6)")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_curated = models.BooleanField(default=False, 
                                    help_text="Whether this is a manually curated suggestion")
    is_featured = models.BooleanField(default=False,
                                     help_text="Whether to feature this suggestion prominently")
    
    # Quality metrics
    avg_confidence = models.FloatField(default=0.0,
                                      help_text="Average confidence score for this query")
    avg_feedback_rating = models.FloatField(null=True, blank=True,
                                          help_text="Average user feedback rating")
    
    # Trending metrics
    recent_count = models.PositiveIntegerField(default=0,
                                             help_text="Usage count in the last 7 days")
    recent_success_count = models.PositiveIntegerField(default=0,
                                                    help_text="Success count in the last 7 days")
    trending_score = models.FloatField(default=0.0,
                                      help_text="Score indicating how trending this query is")
    
    class Meta:
        verbose_name = "Query Suggestion"
        verbose_name_plural = "Query Suggestions"
        indexes = [
            models.Index(fields=['query_text']),
            models.Index(fields=['doc_type']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['trending_score']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.query_text
    
    def increment_usage(self, success=False):
        """
        Increment usage count and success count if the query was successful.
        
        Args:
            success (bool): Whether the query resulted in a successful answer
        """
        self.usage_count += 1
        self.recent_count += 1
        
        if success:
            self.success_count += 1
            self.recent_success_count += 1
            
        self.save()
    
    def update_metrics(self, confidence_score=None, feedback_rating=None):
        """
        Update quality metrics for this query suggestion.
        
        Args:
            confidence_score (float): Confidence score from the latest answer
            feedback_rating (float): User feedback rating
        """
        if confidence_score is not None:
            # Update average confidence with exponential moving average
            alpha = 0.3  # Weight for new value
            self.avg_confidence = (alpha * confidence_score + 
                                 (1 - alpha) * self.avg_confidence)
        
        if feedback_rating is not None:
            # Update average feedback rating
            if self.avg_feedback_rating is None:
                self.avg_feedback_rating = feedback_rating
            else:
                alpha = 0.3  # Weight for new value
                self.avg_feedback_rating = (alpha * feedback_rating + 
                                          (1 - alpha) * self.avg_feedback_rating)
        
        self.save()


class QueryCompletion(models.Model):
    """
    Model for storing query completions for auto-complete functionality.
    These are more granular than full query suggestions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prefix = models.CharField(max_length=100, db_index=True,
                            help_text="The query prefix for autocompletion")
    completion = models.CharField(max_length=512,
                                help_text="The suggested completion")
    frequency = models.PositiveIntegerField(default=1,
                                          help_text="How often this completion appears")
    doc_type = models.CharField(max_length=50, blank=True,
                               help_text="Document type this completion is most relevant for")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Query Completion"
        verbose_name_plural = "Query Completions"
        unique_together = ('prefix', 'completion')
        indexes = [
            models.Index(fields=['prefix']),
            models.Index(fields=['frequency']),
        ]
    
    def __str__(self):
        return f"{self.prefix} → {self.completion}"


class SearchRankingProfile(models.Model):
    """
    Model for storing custom search ranking profiles.
    These can be used to adjust search relevance for different use cases.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Vector vs. keyword search parameters
    use_hybrid = models.BooleanField(default=True,
                                   help_text="Whether to use hybrid search (vector + keyword)")
    hybrid_alpha = models.FloatField(default=0.75,
                                   help_text="Weight for vector search (0-1)")
    
    # Filtering parameters
    doc_type_weights = models.JSONField(default=dict, blank=True,
                                      help_text="Weight multipliers for different doc types")
    recency_boost = models.FloatField(default=0.0,
                                    help_text="Boost for more recent documents (0-1)")
    
    # Reranking parameters
    use_reranking = models.BooleanField(default=True,
                                      help_text="Whether to use cross-encoder reranking")
    reranking_factor = models.FloatField(default=1.0,
                                       help_text="Weight for reranking scores")
    
    # Additional parameters
    results_limit = models.PositiveIntegerField(default=10,
                                              help_text="Default number of results to return")
    include_figures = models.BooleanField(default=True,
                                        help_text="Whether to include figures in results")
    
    # Status and usage
    is_default = models.BooleanField(default=False,
                                   help_text="Whether this is the default profile")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.PositiveIntegerField(default=0,
                                            help_text="Number of times this profile has been used")
    
    class Meta:
        verbose_name = "Search Ranking Profile"
        verbose_name_plural = "Search Ranking Profiles"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure hybrid_alpha is between 0 and 1
        self.hybrid_alpha = max(0.0, min(1.0, self.hybrid_alpha))
        
        # Ensure recency_boost is between 0 and 1
        self.recency_boost = max(0.0, min(1.0, self.recency_boost))
        
        # If this profile is being set as default, unset any other defaults
        if self.is_default:
            SearchRankingProfile.objects.filter(is_default=True).update(is_default=False)
            
        super().save(*args, **kwargs)
    
    def increment_usage(self):
        """Increment the usage count for this profile."""
        self.usage_count += 1
        self.save(update_fields=['usage_count', 'updated_at'])


class SearchFilter(models.Model):
    """
    Model for custom search filters that can be applied to search queries.
    These can be predefined filters or user-created filters.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Filter criteria (stored as JSON)
    filter_type = models.CharField(max_length=50, choices=[
        ('basic', 'Basic Filter'),
        ('complex', 'Complex Filter'),
        ('semantic', 'Semantic Filter'),
    ])
    filter_criteria = models.JSONField(
        help_text="JSON object describing filter criteria"
    )
    
    # Metadata
    is_system = models.BooleanField(default=False,
                                  help_text="Whether this is a system-defined filter")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Search Filter"
        verbose_name_plural = "Search Filters"
        unique_together = ('name', 'created_by')  # Allow same name for different users
    
    def __str__(self):
        return self.name


class SearchFacet(models.Model):
    """
    Model for defining facets that can be used for faceted search.
    Facets are dimensions that can be used to categorize and filter search results.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    field_path = models.CharField(max_length=100,
                                help_text="Path to the field in Weaviate schema")
    
    # Facet configuration
    facet_type = models.CharField(max_length=50, choices=[
        ('categorical', 'Categorical'),
        ('numerical', 'Numerical Range'),
        ('temporal', 'Date/Time Range'),
        ('hierarchical', 'Hierarchical'),
    ])
    
    # Additional configuration options
    config = models.JSONField(default=dict, blank=True,
                           help_text="Additional configuration for this facet")
    
    # Display options
    display_order = models.PositiveIntegerField(default=0,
                                             help_text="Order for display in the UI")
    is_default = models.BooleanField(default=False,
                                   help_text="Whether to show this facet by default")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Search Facet"
        verbose_name_plural = "Search Facets"
        ordering = ['display_order', 'display_name']
    
    def __str__(self):
        return self.display_name


class SavedSearch(models.Model):
    """
    Model for storing saved searches that users can revisit.
    Includes search query, filters, facets, and ranking profile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # The user who created this saved search
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    
    # Search configuration
    query_text = models.TextField(blank=True)
    filters = models.ManyToManyField(SearchFilter, blank=True)
    ranking_profile = models.ForeignKey(SearchRankingProfile, on_delete=models.SET_NULL,
                                      null=True, blank=True)
    
    # Additional parameters (stored as JSON)
    parameters = models.JSONField(default=dict, blank=True,
                               help_text="Additional search parameters")
    
    # Usage tracking
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Saved Search"
        verbose_name_plural = "Saved Searches"
        unique_together = ('name', 'user')  # Allow same name for different users
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"


class SearchAnalytics(models.Model):
    """
    Model for tracking detailed search analytics beyond basic metrics.
    Useful for analyzing search performance and improving search over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query_text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True,
                                help_text="Session identifier for anonymous users")
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Search parameters
    doc_type = models.CharField(max_length=50, blank=True)
    use_hybrid = models.BooleanField(default=True)
    hybrid_alpha = models.FloatField(null=True, blank=True)
    ranking_profile = models.ForeignKey(SearchRankingProfile, on_delete=models.SET_NULL, 
                                       null=True, blank=True)
    applied_filters = models.JSONField(default=list, blank=True,
                                    help_text="Filters applied to this search")
    applied_facets = models.JSONField(default=list, blank=True,
                                   help_text="Facets applied to this search")
    
    # Results
    num_results = models.PositiveIntegerField(default=0,
                                           help_text="Number of results returned")
    top_doc_types = models.JSONField(default=list, blank=True,
                                  help_text="Document types in top results")
    answer_generated = models.BooleanField(default=True,
                                        help_text="Whether an answer was generated")
    confidence_score = models.FloatField(null=True, blank=True)
    
    # User interaction
    result_selected = models.BooleanField(null=True, blank=True,
                                       help_text="Whether the user selected a result")
    time_to_first_click = models.PositiveIntegerField(null=True, blank=True,
                                                  help_text="Time to first click in ms")
    
    # Performance
    search_time_ms = models.PositiveIntegerField(null=True, blank=True,
                                               help_text="Time taken for search in ms")
    reranking_time_ms = models.PositiveIntegerField(null=True, blank=True,
                                                  help_text="Time taken for reranking in ms")
    answer_time_ms = models.PositiveIntegerField(null=True, blank=True,
                                               help_text="Time taken for answer generation in ms")
    
    # Related objects
    query_history = models.ForeignKey(QueryHistory, on_delete=models.SET_NULL, 
                                    null=True, blank=True)
    saved_search = models.ForeignKey(SavedSearch, on_delete=models.SET_NULL,
                                   null=True, blank=True)
    
    class Meta:
        verbose_name = "Search Analytics"
        verbose_name_plural = "Search Analytics"
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['query_text']),
            models.Index(fields=['doc_type']),
        ]
    
    def __str__(self):
        return f"Search: {self.query_text[:30]}..."