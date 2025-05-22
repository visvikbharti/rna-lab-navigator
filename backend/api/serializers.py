from rest_framework import serializers
from .models import (
    Document, 
    QueryHistory, 
    Feedback, 
    QueryCache,
    EvaluationSet,
    ReferenceQuestion,
    EvaluationRun,
    QuestionResult,
    Figure
)


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"


class DocumentPreviewSerializer(serializers.ModelSerializer):
    """Serializer for document preview data"""
    preview_text = serializers.CharField(required=False, read_only=True)
    citation = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'doc_type', 'author', 'year', 
            'created_at', 'updated_at', 'preview_text', 'citation'
        ]
    
    def get_citation(self, obj):
        """Generate a citation string for the document"""
        citation = f"{obj.title}"
        
        if obj.author:
            citation += f", by {obj.author}"
            
        if obj.year:
            citation += f" ({obj.year})"
            
        return citation


class QuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=True)
    doc_type = serializers.CharField(required=False, allow_blank=True)
    use_hybrid = serializers.BooleanField(required=False, default=True)
    hybrid_alpha = serializers.FloatField(required=False, default=0.75)
    use_cache = serializers.BooleanField(required=False, default=True)
    model_tier = serializers.CharField(required=False, default="default")


class QueryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryHistory
        fields = "__all__"


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for user feedback on answers"""
    query_text = serializers.CharField(source='query_history.query_text', read_only=True)
    answer = serializers.CharField(source='query_history.answer', read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'query_history', 'query_text', 'answer', 'rating', 
            'comment', 'specific_issues', 'retrieval_quality', 
            'answer_relevance', 'citation_accuracy', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user feedback with query_id instead of query_history object"""
    query_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'query_id', 'rating', 'comment', 'specific_issues',
            'retrieval_quality', 'answer_relevance', 'citation_accuracy'
        ]
    
    def create(self, validated_data):
        # Extract query_id and get the query_history object
        query_id = validated_data.pop('query_id')
        try:
            query_history = QueryHistory.objects.get(id=query_id)
        except QueryHistory.DoesNotExist:
            raise serializers.ValidationError({"query_id": "Query not found"})
        
        # Create the feedback object
        return Feedback.objects.create(
            query_history=query_history,
            **validated_data
        )


class QueryCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryCache
        fields = [
            'id', 'query_text', 'doc_type', 'answer', 'sources',
            'confidence_score', 'hit_count', 'created_at', 'last_accessed'
        ]
        read_only_fields = ['id', 'hit_count', 'created_at', 'last_accessed']


class ReferenceQuestionSerializer(serializers.ModelSerializer):
    """Serializer for reference questions used in evaluations"""
    class Meta:
        model = ReferenceQuestion
        fields = [
            'id', 'evaluation_set', 'question_text', 'question_type',
            'expected_answer', 'expected_sources', 'doc_type', 'difficulty'
        ]


class EvaluationSetSerializer(serializers.ModelSerializer):
    """Serializer for evaluation sets"""
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EvaluationSet
        fields = [
            'id', 'name', 'description', 'created_at', 
            'updated_at', 'is_active', 'question_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'question_count']
    
    def get_question_count(self, obj):
        return obj.questions.count()


class QuestionResultSerializer(serializers.ModelSerializer):
    """Serializer for individual question results in an evaluation"""
    question_text = serializers.CharField(source='reference_question.question_text', read_only=True)
    
    class Meta:
        model = QuestionResult
        fields = [
            'id', 'evaluation_run', 'reference_question', 'question_text',
            'answer', 'sources', 'confidence_score', 'retrieval_precision',
            'answer_relevance', 'execution_time', 'model_used'
        ]
        read_only_fields = ['id', 'question_text']


class EvaluationRunSerializer(serializers.ModelSerializer):
    """Serializer for evaluation runs"""
    evaluation_set_name = serializers.CharField(source='evaluation_set.name', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = EvaluationRun
        fields = [
            'id', 'evaluation_set', 'evaluation_set_name', 'run_date', 'status',
            'average_score', 'average_retrieval_precision', 'average_answer_relevance',
            'total_questions', 'success_count', 'failure_count', 'success_rate',
            'execution_time', 'notes'
        ]
        read_only_fields = [
            'id', 'run_date', 'average_score', 'average_retrieval_precision',
            'average_answer_relevance', 'total_questions', 'success_count',
            'failure_count', 'execution_time', 'success_rate'
        ]
    
    def get_success_rate(self, obj):
        if obj.total_questions > 0:
            return obj.success_count / obj.total_questions
        return 0


class TriggerEvaluationSerializer(serializers.Serializer):
    """Serializer for triggering a new evaluation run"""
    evaluation_set_id = serializers.IntegerField(required=True)
    use_hybrid = serializers.BooleanField(required=False, default=True)
    use_cache = serializers.BooleanField(required=False, default=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class EvaluationReportSerializer(serializers.Serializer):
    """Serializer for detailed evaluation reports"""
    # This is a read-only serializer for the report data structure
    run_id = serializers.IntegerField()
    set_name = serializers.CharField()
    run_date = serializers.DateTimeField()
    status = serializers.CharField()
    summary = serializers.DictField()
    by_question_type = serializers.DictField()
    best_performers = serializers.ListField()
    worst_performers = serializers.ListField()


class FigureSerializer(serializers.ModelSerializer):
    """Serializer for extracted figures from documents"""
    document_title = serializers.CharField(source='document.title', read_only=True)
    document_author = serializers.CharField(source='document.author', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Figure
        fields = [
            'id', 'figure_id', 'figure_type', 'caption', 'page_number',
            'document', 'document_title', 'document_author', 'file_url',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'file_url', 'created_at']
    
    def get_file_url(self, obj):
        """Get the URL for the figure file"""
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request is not None:
            return request.build_absolute_uri(obj.file.url)
        return None