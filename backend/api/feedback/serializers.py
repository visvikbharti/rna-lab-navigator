"""
Serializers for the enhanced feedback system.
"""

from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    EnhancedFeedback,
    FeedbackCategory,
    FeedbackTheme,
    FeedbackAnalysis,
    FeedbackThemeMapping
)
from ..models import QueryHistory


class EnhancedFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for displaying enhanced feedback details"""
    
    query_text = serializers.CharField(source='query_history.query_text', read_only=True)
    answer = serializers.CharField(source='query_history.answer', read_only=True)
    confidence_score = serializers.FloatField(source='query_history.confidence_score', read_only=True)
    sources = serializers.JSONField(source='query_history.sources', read_only=True)
    username = serializers.SerializerMethodField()
    reviewer_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = EnhancedFeedback
        fields = [
            'id', 'query_history', 'query_text', 'answer', 'confidence_score', 'sources',
            'user', 'username', 'rating', 'category', 'status', 'comment', 'specific_issues',
            'relevance_rating', 'accuracy_rating', 'completeness_rating', 'clarity_rating',
            'citation_rating', 'average_rating', 'incorrect_sections', 'suggested_answer',
            'source_quality_issues', 'reviewed_by', 'reviewer_name', 'reviewed_at',
            'review_notes', 'system_response', 'improvement_actions', 'system_response_date',
            'created_at'
        ]
        read_only_fields = [
            'id', 'query_text', 'answer', 'confidence_score', 'sources', 'username',
            'reviewer_name', 'average_rating', 'created_at', 'reviewed_at', 'system_response_date'
        ]
    
    def get_username(self, obj):
        """Get username if available"""
        if obj.user:
            return obj.user.username
        return None
    
    def get_reviewer_name(self, obj):
        """Get reviewer name if available"""
        if obj.reviewed_by:
            return obj.reviewed_by.username
        return None
    
    def get_average_rating(self, obj):
        """Calculate average of all numeric ratings"""
        ratings = []
        for field in ['relevance_rating', 'accuracy_rating', 'completeness_rating', 
                     'clarity_rating', 'citation_rating']:
            value = getattr(obj, field)
            if value is not None:
                ratings.append(value)
        
        if not ratings:
            return None
        
        return sum(ratings) / len(ratings)


class EnhancedFeedbackCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating enhanced feedback with query_id instead of query_history object"""
    
    query_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = EnhancedFeedback
        fields = [
            'query_id', 'user', 'rating', 'category', 'comment', 'specific_issues',
            'relevance_rating', 'accuracy_rating', 'completeness_rating', 'clarity_rating',
            'citation_rating', 'incorrect_sections', 'suggested_answer', 'source_quality_issues'
        ]
    
    def create(self, validated_data):
        """Create the feedback with query_history from query_id"""
        # Extract query_id and get the query_history object
        query_id = validated_data.pop('query_id')
        try:
            query_history = QueryHistory.objects.get(id=query_id)
        except QueryHistory.DoesNotExist:
            raise serializers.ValidationError({"query_id": "Query not found"})
        
        # Create the feedback object
        return EnhancedFeedback.objects.create(
            query_history=query_history,
            **validated_data
        )


class EnhancedFeedbackUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating feedback status and review information"""
    
    class Meta:
        model = EnhancedFeedback
        fields = [
            'status', 'review_notes', 'system_response', 'improvement_actions'
        ]


class FeedbackCategorySerializer(serializers.ModelSerializer):
    """Serializer for feedback categories"""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedbackCategory
        fields = [
            'id', 'name', 'description', 'type', 'parent', 'children',
            'is_active', 'display_order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_children(self, obj):
        """Get child categories if any"""
        children = obj.children.filter(is_active=True).order_by('display_order', 'name')
        if not children:
            return []
        
        # Use a simplified serializer to avoid circular reference
        return SimpleFeedbackCategorySerializer(children, many=True).data


class SimpleFeedbackCategorySerializer(serializers.ModelSerializer):
    """Simplified serializer for feedback categories (without children)"""
    
    class Meta:
        model = FeedbackCategory
        fields = ['id', 'name', 'description', 'type', 'is_active', 'display_order']


class FeedbackThemeSerializer(serializers.ModelSerializer):
    """Serializer for feedback themes"""
    
    assigned_to_name = serializers.SerializerMethodField()
    feedback_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedbackTheme
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'feedback_count',
            'first_reported', 'last_reported', 'assigned_to', 'assigned_to_name',
            'solution_notes', 'resolution_date', 'tags'
        ]
        read_only_fields = ['id', 'first_reported', 'last_reported', 'feedback_count']
    
    def get_assigned_to_name(self, obj):
        """Get the name of the assigned user"""
        if obj.assigned_to:
            return obj.assigned_to.username
        return None
    
    def get_feedback_count(self, obj):
        """Get the actual count of feedback items"""
        return obj.feedback_mappings.count()


class FeedbackAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for feedback analysis"""
    
    implemented_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedbackAnalysis
        fields = [
            'id', 'analysis_id', 'date_range_start', 'date_range_end', 'analysis_date',
            'total_feedback_analyzed', 'positive_feedback_count', 'negative_feedback_count',
            'neutral_feedback_count', 'top_issues', 'category_distribution',
            'improvement_opportunities', 'trend_analysis', 'recommended_actions',
            'priority_areas', 'actions_implemented', 'implementation_date',
            'implemented_by', 'implemented_by_name', 'effectiveness_metrics'
        ]
        read_only_fields = ['id', 'analysis_id', 'analysis_date']
    
    def get_implemented_by_name(self, obj):
        """Get the name of the implementing user"""
        if obj.implemented_by:
            return obj.implemented_by.username
        return None


class FeedbackThemeMappingSerializer(serializers.ModelSerializer):
    """Serializer for mapping feedback to themes"""
    
    feedback_summary = serializers.SerializerMethodField()
    theme_title = serializers.CharField(source='theme.title', read_only=True)
    mapped_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedbackThemeMapping
        fields = [
            'id', 'feedback', 'feedback_summary', 'theme', 'theme_title',
            'mapped_at', 'mapped_by', 'mapped_by_name', 'relevance_score', 'notes'
        ]
        read_only_fields = ['id', 'mapped_at', 'feedback_summary', 'theme_title', 'mapped_by_name']
    
    def get_feedback_summary(self, obj):
        """Get a summary of the feedback"""
        return {
            'id': obj.feedback.id,
            'rating': obj.feedback.rating,
            'category': obj.feedback.category,
            'query_text': obj.feedback.query_history.query_text[:100]
        }
    
    def get_mapped_by_name(self, obj):
        """Get the name of the user who created the mapping"""
        if obj.mapped_by:
            return obj.mapped_by.username
        return None