from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from api.models import Document

User = get_user_model()


class ResearchHypothesis(models.Model):
    """AI-generated research hypotheses based on literature analysis"""
    
    title = models.CharField(max_length=500)
    description = models.TextField()
    rationale = models.TextField(help_text="Why this hypothesis is worth exploring")
    
    # Testability and feasibility scores
    testability_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How easily this can be tested experimentally"
    )
    novelty_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How novel/unique this hypothesis is"
    )
    impact_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Potential impact if proven true"
    )
    
    # Supporting evidence
    supporting_papers = models.ManyToManyField(Document, related_name='hypotheses')
    contradicting_papers = models.ManyToManyField(Document, related_name='contradicting_hypotheses', blank=True)
    
    # Knowledge gaps this addresses
    knowledge_gaps = models.JSONField(default=list)
    
    # Suggested experimental approaches
    experimental_approaches = models.JSONField(default=list)
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # User feedback
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    tested_by_labs = models.JSONField(default=list, help_text="Labs that tested this hypothesis")
    
    class Meta:
        ordering = ['-impact_score', '-novelty_score', '-created_at']
        indexes = [
            models.Index(fields=['impact_score', 'novelty_score']),
            models.Index(fields=['created_at']),
        ]


class ExperimentPrediction(models.Model):
    """Predictions for experimental outcomes based on similar studies"""
    
    experiment_title = models.CharField(max_length=500)
    experiment_description = models.TextField()
    
    # Core prediction
    predicted_outcome = models.TextField()
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Experimental design recommendations
    recommended_controls = models.JSONField(default=list)
    recommended_variables = models.JSONField(default=list)
    sample_size_recommendation = models.IntegerField(null=True, blank=True)
    
    # Technical recommendations
    recommended_techniques = models.JSONField(default=list)
    potential_pitfalls = models.JSONField(default=list)
    optimization_suggestions = models.JSONField(default=list)
    
    # Success probability factors
    success_factors = models.JSONField(default=dict)
    risk_factors = models.JSONField(default=dict)
    
    # Similar experiments used for prediction
    similar_experiments = models.ManyToManyField(Document, related_name='used_for_predictions')
    
    # Timeline and resources
    estimated_duration_days = models.IntegerField(null=True, blank=True)
    estimated_cost_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    required_equipment = models.JSONField(default=list)
    required_expertise = models.JSONField(default=list)
    
    # Metadata
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Feedback after experiment
    actual_outcome = models.TextField(blank=True)
    outcome_matched = models.BooleanField(null=True)
    feedback_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']


class CrossStudyInsight(models.Model):
    """Hidden connections and insights across multiple studies"""
    
    INSIGHT_TYPES = [
        ('connection', 'Hidden Connection'),
        ('contradiction', 'Contradictory Results'),
        ('pattern', 'Emerging Pattern'),
        ('gap', 'Knowledge Gap'),
        ('opportunity', 'Collaboration Opportunity'),
    ]
    
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=500)
    description = models.TextField()
    
    # Studies involved
    primary_studies = models.ManyToManyField(Document, related_name='primary_insights')
    supporting_studies = models.ManyToManyField(Document, related_name='supporting_insights', blank=True)
    
    # Analysis details
    connection_strength = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    evidence_quality = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Specific findings
    key_findings = models.JSONField(default=list)
    statistical_analysis = models.JSONField(default=dict, blank=True)
    
    # For contradictions
    contradiction_details = models.JSONField(default=dict, blank=True)
    possible_explanations = models.JSONField(default=list, blank=True)
    
    # For collaboration opportunities
    suggested_collaborators = models.JSONField(default=list, blank=True)
    collaboration_rationale = models.TextField(blank=True)
    
    # Knowledge network mapping
    knowledge_domains = models.JSONField(default=list)
    technique_overlap = models.JSONField(default=list)
    
    # Metadata
    discovered_at = models.DateTimeField(auto_now_add=True)
    validated = models.BooleanField(default=False)
    validation_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-connection_strength', '-discovered_at']
        indexes = [
            models.Index(fields=['insight_type', 'connection_strength']),
        ]


class ResearchTimeline(models.Model):
    """Optimized research timeline for a series of experiments"""
    
    project_name = models.CharField(max_length=500)
    project_description = models.TextField()
    
    # Timeline optimization
    total_duration_days = models.IntegerField()
    critical_path = models.JSONField(help_text="Ordered list of critical experiments")
    parallel_tracks = models.JSONField(help_text="Experiments that can run in parallel")
    
    # Dependencies
    experiment_dependencies = models.JSONField(
        help_text="Graph of experiment dependencies"
    )
    
    # Resource optimization
    resource_allocation = models.JSONField(
        help_text="Optimal allocation of equipment/personnel over time"
    )
    bottleneck_analysis = models.JSONField(
        help_text="Identified bottlenecks and mitigation strategies"
    )
    
    # Milestones
    milestones = models.JSONField(default=list)
    decision_points = models.JSONField(
        default=list,
        help_text="Key decision points where direction might change"
    )
    
    # Risk analysis
    risk_assessment = models.JSONField(default=dict)
    contingency_plans = models.JSONField(default=dict)
    
    # Cost optimization
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_breakdown = models.JSONField(default=dict)
    cost_saving_suggestions = models.JSONField(default=list)
    
    # Related hypotheses and experiments
    hypotheses = models.ManyToManyField(ResearchHypothesis, related_name='timelines')
    experiments = models.ManyToManyField(ExperimentPrediction, related_name='timelines')
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Execution tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_experiments = models.JSONField(default=list)
    current_phase = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']


class ResearchInsightFeedback(models.Model):
    """Track feedback on AI-generated insights"""
    
    FEEDBACK_TYPES = [
        ('hypothesis', 'Hypothesis Feedback'),
        ('prediction', 'Prediction Feedback'),
        ('insight', 'Cross-Study Insight Feedback'),
        ('timeline', 'Timeline Feedback'),
    ]
    
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    
    # Polymorphic reference to the insight
    hypothesis = models.ForeignKey(ResearchHypothesis, on_delete=models.CASCADE, null=True, blank=True)
    prediction = models.ForeignKey(ExperimentPrediction, on_delete=models.CASCADE, null=True, blank=True)
    insight = models.ForeignKey(CrossStudyInsight, on_delete=models.CASCADE, null=True, blank=True)
    timeline = models.ForeignKey(ResearchTimeline, on_delete=models.CASCADE, null=True, blank=True)
    
    # Feedback details
    usefulness_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    accuracy_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    comments = models.TextField()
    specific_improvements = models.JSONField(default=list)
    
    # For tested hypotheses/predictions
    was_tested = models.BooleanField(default=False)
    test_results = models.TextField(blank=True)
    
    # Metadata
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['feedback_type', 'usefulness_rating']),
        ]