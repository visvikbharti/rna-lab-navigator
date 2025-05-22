from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import os


class Document(models.Model):
    """Base model for all documents stored in the system."""
    
    DOCUMENT_TYPES = (
        ("thesis", "Thesis"),
        ("protocol", "Protocol"),
        ("paper", "Paper"),
        ("inventory", "Inventory"),
    )
    
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    author = models.CharField(max_length=255, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.doc_type})"


class QueryHistory(models.Model):
    """Model to track query history and performance."""
    
    query_text = models.TextField()
    answer = models.TextField()
    confidence_score = models.FloatField()
    sources = models.JSONField(default=list)
    processing_time = models.FloatField(null=True, blank=True, help_text="Query processing time in seconds")
    doc_type = models.CharField(max_length=20, blank=True, help_text="Type of document queried")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Query: {self.query_text[:50]}... (Score: {self.confidence_score:.2f})"


class Feedback(models.Model):
    """
    Model to track user feedback on answers for continual improvement.
    Linked to QueryHistory for full context.
    """
    
    RATING_CHOICES = (
        ('thumbs_up', 'Thumbs Up'),
        ('thumbs_down', 'Thumbs Down'),
    )
    
    query_history = models.ForeignKey(
        QueryHistory,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    rating = models.CharField(max_length=15, choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    specific_issues = models.JSONField(blank=True, null=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional numerical ratings for specific aspects
    retrieval_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Rating for the quality of retrieved information (1-5)"
    )
    answer_relevance = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Rating for the relevance of the answer to the query (1-5)"
    )
    citation_accuracy = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Rating for the accuracy of citations in the answer (1-5)"
    )
    
    def __str__(self):
        return f"{self.rating} on '{self.query_history.query_text[:30]}...'"
    
    class Meta:
        verbose_name = "User Feedback"
        verbose_name_plural = "User Feedback"
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]


class QueryCache(models.Model):
    """
    Model to cache frequently asked queries and their responses.
    Reduces API costs and improves response time.
    """
    
    query_hash = models.CharField(max_length=64, unique=True, db_index=True)
    query_text = models.TextField()
    doc_type = models.CharField(max_length=20, blank=True)
    answer = models.TextField()
    sources = models.JSONField(default=list)
    confidence_score = models.FloatField()
    hit_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cache: {self.query_text[:40]}... (Hits: {self.hit_count})"
    
    class Meta:
        indexes = [
            models.Index(fields=['query_hash']),
            models.Index(fields=['last_accessed']),
            models.Index(fields=['hit_count']),
        ]


class EvaluationSet(models.Model):
    """
    Model to store sets of reference questions and expected answers
    for automated system evaluation.
    """
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Evaluation Set"
        verbose_name_plural = "Evaluation Sets"


class ReferenceQuestion(models.Model):
    """
    Model for storing reference questions with expected answers
    for automated evaluation.
    """
    
    QUESTION_TYPES = (
        ('factoid', 'Factoid'),
        ('explanation', 'Explanation'),
        ('comparison', 'Comparison'),
        ('procedure', 'Procedure'),
        ('context', 'Contextual'),
    )
    
    evaluation_set = models.ForeignKey(
        EvaluationSet, 
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    expected_answer = models.TextField()
    expected_sources = models.JSONField(default=list)
    doc_type = models.CharField(max_length=20, blank=True)
    difficulty = models.PositiveIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Difficulty level (1-5)"
    )
    
    def __str__(self):
        return f"{self.question_text[:50]}..."
    
    class Meta:
        verbose_name = "Reference Question"
        verbose_name_plural = "Reference Questions"


class EvaluationRun(models.Model):
    """
    Model to store evaluation run results.
    Each run evaluates all questions in an evaluation set.
    """
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    evaluation_set = models.ForeignKey(
        EvaluationSet,
        on_delete=models.CASCADE,
        related_name='runs'
    )
    run_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    average_score = models.FloatField(null=True, blank=True)
    average_retrieval_precision = models.FloatField(null=True, blank=True)
    average_answer_relevance = models.FloatField(null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    execution_time = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Run: {self.evaluation_set.name} - {self.run_date.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = "Evaluation Run"
        verbose_name_plural = "Evaluation Runs"
        ordering = ['-run_date']


class QuestionResult(models.Model):
    """
    Model to store individual question results within an evaluation run.
    """
    
    evaluation_run = models.ForeignKey(
        EvaluationRun,
        on_delete=models.CASCADE,
        related_name='results'
    )
    reference_question = models.ForeignKey(
        ReferenceQuestion,
        on_delete=models.CASCADE,
        related_name='results'
    )
    answer = models.TextField()
    sources = models.JSONField(default=list)
    confidence_score = models.FloatField()
    retrieval_precision = models.FloatField()
    answer_relevance = models.FloatField()
    execution_time = models.FloatField(null=True, blank=True)
    model_used = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"Result: {self.reference_question.question_text[:40]}..."
    
    class Meta:
        verbose_name = "Question Result"
        verbose_name_plural = "Question Results"


def figure_upload_path(instance, filename):
    """Define path for figure uploads"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('figures', filename)


class Figure(models.Model):
    """
    Model to store extracted figures from documents with their captions
    and metadata for retrieval and display.
    """
    
    FIGURE_TYPES = (
        ('image', 'Image'),
        ('chart', 'Chart'),
        ('graph', 'Graph'),
        ('table', 'Table'),
        ('diagram', 'Diagram'),
    )
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='figures'
    )
    figure_id = models.CharField(max_length=100, unique=True)
    figure_type = models.CharField(max_length=20, choices=FIGURE_TYPES)
    caption = models.TextField(blank=True)
    page_number = models.PositiveIntegerField()
    file = models.FileField(upload_to=figure_upload_path)
    embedding_vector = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.figure_type} from {self.document.title} (p.{self.page_number})"
    
    class Meta:
        verbose_name = "Extracted Figure"
        verbose_name_plural = "Extracted Figures"
        indexes = [
            models.Index(fields=['figure_type']),
            models.Index(fields=['document']),
        ]