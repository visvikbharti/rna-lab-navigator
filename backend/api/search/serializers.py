from rest_framework import serializers
from .models import (
    QuerySuggestion, 
    QueryCompletion, 
    SearchRankingProfile, 
    SearchAnalytics,
    SearchFilter,
    SearchFacet,
    SavedSearch
)

class QuerySuggestionSerializer(serializers.ModelSerializer):
    """Serializer for query suggestions."""
    class Meta:
        model = QuerySuggestion
        fields = [
            'id', 'query_text', 'category', 'usage_count', 'success_rate',
            'created_at', 'last_used', 'is_curated', 'embedding'
        ]
        read_only_fields = ['usage_count', 'success_rate', 'last_used']


class QueryCompletionSerializer(serializers.ModelSerializer):
    """Serializer for query completions."""
    class Meta:
        model = QueryCompletion
        fields = ['id', 'prefix', 'completion', 'usage_count', 'created_at', 'last_used']
        read_only_fields = ['usage_count', 'last_used']


class SearchRankingProfileSerializer(serializers.ModelSerializer):
    """Serializer for search ranking profiles."""
    class Meta:
        model = SearchRankingProfile
        fields = [
            'id', 'name', 'description', 'use_hybrid', 'hybrid_alpha', 
            'doc_type_weights', 'recency_boost', 'use_reranking',
            'reranking_factor', 'results_limit', 'include_figures',
            'is_default', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SearchFilterSerializer(serializers.ModelSerializer):
    """Serializer for search filters."""
    class Meta:
        model = SearchFilter
        fields = [
            'id', 'name', 'description', 'filter_type', 'filter_criteria',
            'is_system', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SearchFacetSerializer(serializers.ModelSerializer):
    """Serializer for search facets."""
    class Meta:
        model = SearchFacet
        fields = [
            'id', 'name', 'display_name', 'field_path', 'facet_type',
            'config', 'display_order', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SavedSearchSerializer(serializers.ModelSerializer):
    """Serializer for saved searches."""
    class Meta:
        model = SavedSearch
        fields = [
            'id', 'name', 'description', 'query_text', 'ranking_profile',
            'parameters', 'last_used', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_used', 'usage_count']


class SearchAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for search analytics."""
    class Meta:
        model = SearchAnalytics
        fields = [
            'id', 'query_text', 'user', 'session_id', 'timestamp',
            'doc_type', 'use_hybrid', 'hybrid_alpha', 'ranking_profile',
            'applied_filters', 'applied_facets', 'num_results', 'top_doc_types',
            'answer_generated', 'confidence_score', 'result_selected',
            'time_to_first_click', 'search_time_ms', 'reranking_time_ms',
            'answer_time_ms', 'query_history', 'saved_search'
        ]
        read_only_fields = ['timestamp', 'search_time_ms', 'reranking_time_ms',
                          'answer_time_ms']