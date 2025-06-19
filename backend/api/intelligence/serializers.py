"""
Serializers for Knowledge Gap Intelligence
"""

from rest_framework import serializers


class KnowledgeGapSerializer(serializers.Serializer):
    """Serializer for knowledge gaps."""
    gap_type = serializers.ChoiceField(
        choices=['coverage', 'validation', 'question', 'combination']
    )
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    gap_severity = serializers.ChoiceField(
        choices=['low', 'medium', 'high']
    )
    impact_score = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)
    source = serializers.CharField(required=False)
    metadata = serializers.DictField(required=False)
    

class ResearchOpportunitySerializer(serializers.Serializer):
    """Serializer for research opportunities."""
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    impact_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    difficulty = serializers.ChoiceField(
        choices=['low', 'medium', 'high', 'varies']
    )
    resources_needed = serializers.ListField(
        child=serializers.CharField()
    )
    related_work = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    feasibility_score = serializers.FloatField(
        min_value=0.0, max_value=1.0,
        required=False
    )
    estimated_timeline = serializers.CharField(required=False)
    potential_collaborators = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    funding_opportunities = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )


class GapAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for gap analysis requests."""
    domain = serializers.CharField(max_length=200)
    analysis_type = serializers.ChoiceField(
        choices=['quick', 'comprehensive'],
        default='quick'
    )
    include_opportunities = serializers.BooleanField(default=False)


class TopicEvolutionSerializer(serializers.Serializer):
    """Serializer for topic evolution data."""
    period = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    document_count = serializers.IntegerField()
    topics = serializers.ListField(
        child=serializers.DictField()
    )
    emerging_topics = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class GapDetailSerializer(serializers.Serializer):
    """Serializer for detailed gap information."""
    id = serializers.CharField()
    type = serializers.CharField()
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    claim = serializers.CharField(required=False)
    question = serializers.CharField(required=False)
    source = serializers.CharField(required=False)
    confidence = serializers.FloatField(required=False)
    impact_score = serializers.FloatField(required=False)
    parameters = serializers.DictField(required=False)
    validation_methods = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    potential_approaches = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    related_papers = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    related_work = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    suggested_experiments = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    estimated_resources = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    potential_outcomes = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    next_steps = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    research_plan = serializers.DictField(required=False)
    related_gaps = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )