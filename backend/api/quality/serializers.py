"""
Serializers for the quality improvement API.
"""

from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    QualityAnalysis,
    QualityImprovement,
    ImprovedPrompt,
    RetrievalConfiguration
)


class QualityAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for QualityAnalysis model."""
    
    class Meta:
        model = QualityAnalysis
        fields = '__all__'
        read_only_fields = (
            'analysis_id', 
            'created_at', 
            'started_at', 
            'completed_at',
            'status',
            'feedback_count',
            'identified_issues',
            'issue_frequencies',
            'topic_clusters',
            'primary_issues',
            'difficulty_assessment',
            'quality_score'
        )


class QualityAnalysisDetailSerializer(QualityAnalysisSerializer):
    """Detailed serializer for QualityAnalysis model."""
    
    improvements = serializers.SerializerMethodField()
    
    class Meta(QualityAnalysisSerializer.Meta):
        pass
    
    def get_improvements(self, obj):
        """Get improvement recommendations for this analysis."""
        improvements = obj.improvement_recommendations.all()
        return QualityImprovementBasicSerializer(improvements, many=True).data


class QualityImprovementSerializer(serializers.ModelSerializer):
    """Serializer for QualityImprovement model."""
    
    class Meta:
        model = QualityImprovement
        fields = '__all__'
        read_only_fields = (
            'improvement_id', 
            'created_at', 
            'approved_at',
            'implemented_at',
            'status'
        )


class QualityImprovementBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for QualityImprovement model."""
    
    class Meta:
        model = QualityImprovement
        fields = (
            'improvement_id',
            'title',
            'improvement_type',
            'priority',
            'status',
            'created_at'
        )


class ImprovedPromptSerializer(serializers.ModelSerializer):
    """Serializer for ImprovedPrompt model."""
    
    class Meta:
        model = ImprovedPrompt
        fields = '__all__'
        read_only_fields = (
            'prompt_id', 
            'created_at', 
            'activated_at',
            'status',
            'usage_count',
            'avg_quality_score'
        )


class RetrievalConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for RetrievalConfiguration model."""
    
    class Meta:
        model = RetrievalConfiguration
        fields = '__all__'
        read_only_fields = (
            'config_id', 
            'created_at', 
            'activated_at',
            'status',
            'usage_count',
            'avg_quality_score'
        )


class QualityMetricsSerializer(serializers.Serializer):
    """Serializer for quality metrics."""
    
    period = serializers.CharField()
    total_feedback = serializers.IntegerField()
    satisfaction_rate = serializers.FloatField(required=False)
    quality_score = serializers.FloatField(required=False)
    rating_averages = serializers.DictField(required=False)
    improvements_implemented = serializers.IntegerField(required=False)
    daily_trend = serializers.DictField(required=False)
    message = serializers.CharField(required=False)


class ApproveImprovementSerializer(serializers.Serializer):
    """Serializer for approving improvements."""
    
    improvement_id = serializers.UUIDField()


class ImplementImprovementSerializer(serializers.Serializer):
    """Serializer for implementing improvements."""
    
    improvement_id = serializers.UUIDField()


class CreateAnalysisSerializer(serializers.Serializer):
    """Serializer for creating a quality analysis."""
    
    name = serializers.CharField(max_length=255)
    analysis_type = serializers.ChoiceField(
        choices=QualityAnalysis.ANALYSIS_TYPE_CHOICES,
        default='general'
    )
    days_lookback = serializers.IntegerField(default=30, min_value=1, max_value=365)
    filters = serializers.DictField(required=False)
    
    def validate_name(self, value):
        """Validate that the name is unique."""
        if QualityAnalysis.objects.filter(name=value).exists():
            raise serializers.ValidationError("Analysis with this name already exists.")
        return value