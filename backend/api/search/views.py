from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, F
from django.utils import timezone
from datetime import timedelta

from .models import QuerySuggestion, QueryCompletion, SearchRankingProfile, SearchAnalytics
from .services import QuerySuggestionService, SearchService
from .serializers import (
    QuerySuggestionSerializer, QueryCompletionSerializer,
    SearchRankingProfileSerializer, SearchAnalyticsSerializer
)
from ..serializers import DocumentSerializer

class QuerySuggestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for query suggestions management.
    """
    queryset = QuerySuggestion.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['query_text', 'category']
    ordering_fields = ['usage_count', 'success_rate', 'last_used']
    ordering = ['-usage_count']
    
    def get_serializer_class(self):
        return QuerySuggestionSerializer
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular query suggestions based on usage count."""
        service = QuerySuggestionService()
        limit = request.query_params.get('limit', 10)
        category = request.query_params.get('category', None)
        
        suggestions = service.get_popular_queries(limit=int(limit), category=category)
        return Response(suggestions)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending query suggestions based on recent usage."""
        service = QuerySuggestionService()
        limit = request.query_params.get('limit', 10)
        category = request.query_params.get('category', None)
        days = request.query_params.get('days', 7)
        
        suggestions = service.get_trending_queries(
            limit=int(limit), 
            category=category,
            days=int(days)
        )
        return Response(suggestions)
    
    @action(detail=False, methods=['get'])
    def semantic(self, request):
        """Get semantically similar query suggestions."""
        service = QuerySuggestionService()
        query = request.query_params.get('query', '')
        limit = request.query_params.get('limit', 5)
        
        if not query:
            return Response(
                {"error": "Query parameter 'query' is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        suggestions = service.get_semantic_suggestions(
            query_text=query,
            limit=int(limit)
        )
        return Response(suggestions)
    
    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """Get autocomplete suggestions for a query prefix."""
        service = QuerySuggestionService()
        prefix = request.query_params.get('prefix', '')
        limit = request.query_params.get('limit', 5)
        
        if not prefix:
            return Response(
                {"error": "Query parameter 'prefix' is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        suggestions = service.get_autocomplete_suggestions(
            prefix=prefix,
            limit=int(limit)
        )
        return Response(suggestions)


class SearchRankingProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing search ranking profiles.
    """
    queryset = SearchRankingProfile.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_serializer_class(self):
        return SearchRankingProfileSerializer


class EnhancedSearchViewSet(viewsets.ViewSet):
    """
    ViewSet for performing enhanced searches with ranking profiles, filters, and facets.
    """
    
    def create(self, request):
        """
        Perform an enhanced search with optional ranking profile.
        
        POST parameters:
        - query_text: The search query
        - doc_type: (optional) Document type filter
        - profile_id: (optional) Ranking profile ID
        - limit: (optional) Maximum results to return
        - session_id: (optional) Session ID for analytics
        - filters: (optional) List of filter criteria
        - facets: (optional) List of facet selections
        - saved_search_id: (optional) ID of a saved search to use
        """
        query_text = request.data.get('query_text', '')
        doc_type = request.data.get('doc_type')
        profile_id = request.data.get('profile_id')
        limit = request.data.get('limit', 10)
        session_id = request.data.get('session_id')
        filters = request.data.get('filters')
        facets = request.data.get('facets')
        saved_search_id = request.data.get('saved_search_id')
        
        # When using a saved search, don't require query_text
        if not query_text and not saved_search_id:
            return Response(
                {"error": "Field 'query_text' is required, unless using a saved search"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = SearchService()
        
        try:
            results, metadata = service.enhanced_search(
                query_text=query_text,
                doc_type=doc_type,
                profile_id=profile_id,
                limit=int(limit),
                session_id=session_id,
                user=request.user if request.user.is_authenticated else None,
                filters=filters,
                facets=facets,
                saved_search_id=saved_search_id
            )
            
            # Record that this query was used
            if query_text:
                QuerySuggestionService().record_query_usage(query_text, results)
            
            return Response({
                'results': DocumentSerializer(results, many=True).data,
                'metadata': metadata
            })
        except Exception as e:
            return Response(
                {"error": f"Search error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def feedback(self, request):
        """
        Record user feedback on search results.
        
        POST parameters:
        - query_id: ID of the query (from search metadata)
        - document_id: ID of the document feedback is for
        - feedback_type: One of 'click', 'relevant', 'not_relevant'
        - session_id: (optional) Session ID for analytics
        """
        query_id = request.data.get('query_id')
        document_id = request.data.get('document_id')
        feedback_type = request.data.get('feedback_type')
        session_id = request.data.get('session_id')
        
        if not all([query_id, document_id, feedback_type]):
            return Response(
                {"error": "Fields 'query_id', 'document_id', and 'feedback_type' are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if feedback_type not in ['click', 'relevant', 'not_relevant']:
            return Response(
                {"error": "Field 'feedback_type' must be one of 'click', 'relevant', 'not_relevant'"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = SearchService()
        service.record_search_feedback(
            query_id=query_id,
            document_id=document_id,
            feedback_type=feedback_type,
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None
        )
        
        return Response({"status": "feedback recorded"})


class SearchFacetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for accessing available search facets.
    """
    queryset = SearchFacet.objects.all().order_by('display_order', 'display_name')
    
    def get_serializer_class(self):
        from .serializers import SearchFacetSerializer
        return SearchFacetSerializer
    
    @action(detail=False, methods=['get'])
    def defaults(self, request):
        """Get default facets that should be shown by default."""
        default_facets = SearchFacet.objects.filter(is_default=True)
        serializer = self.get_serializer(default_facets, many=True)
        return Response(serializer.data)


class SavedSearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing saved searches.
    """
    
    def get_queryset(self):
        # Only return saved searches for the authenticated user
        user = self.request.user
        if user.is_authenticated:
            return SavedSearch.objects.filter(user=user).order_by('-last_used')
        return SavedSearch.objects.none()
    
    def get_serializer_class(self):
        from .serializers import SavedSearchSerializer
        return SavedSearchSerializer
    
    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            last_used=timezone.now()
        )
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Execute a saved search.
        
        Loads the saved search and performs an enhanced search with its parameters.
        Additional parameters in the request will override those in the saved search.
        """
        saved_search = self.get_object()
        
        # Update usage statistics
        saved_search.usage_count += 1
        saved_search.last_used = timezone.now()
        saved_search.save(update_fields=['usage_count', 'last_used'])
        
        # Get parameters from saved search
        query_text = saved_search.query_text
        profile_id = str(saved_search.ranking_profile.id) if saved_search.ranking_profile else None
        
        # Override with request parameters if provided
        if 'query_text' in request.data:
            query_text = request.data.get('query_text')
        
        if 'profile_id' in request.data:
            profile_id = request.data.get('profile_id')
        
        # Get filters and facets from saved search
        filters = saved_search.parameters.get('filters', [])
        facets = saved_search.parameters.get('facets', [])
        
        # Override with request parameters if provided
        if 'filters' in request.data:
            filters = request.data.get('filters')
            
        if 'facets' in request.data:
            facets = request.data.get('facets')
        
        # Get limit from request or use default
        limit = request.data.get('limit', 10)
        session_id = request.data.get('session_id')
        
        # Perform search
        service = SearchService()
        results, metadata = service.enhanced_search(
            query_text=query_text,
            profile_id=profile_id,
            limit=int(limit),
            session_id=session_id,
            user=request.user,
            filters=filters,
            facets=facets
        )
        
        return Response({
            'results': DocumentSerializer(results, many=True).data,
            'metadata': metadata
        })


class SearchAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for accessing search analytics data.
    """
    queryset = SearchAnalytics.objects.all()
    
    def get_serializer_class(self):
        return SearchAnalyticsSerializer
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """
        Get search performance metrics.
        
        Query parameters:
        - days: Number of days to look back (default 30)
        - group_by: How to group results (default 'day')
        """
        days = int(request.query_params.get('days', 30))
        group_by = request.query_params.get('group_by', 'day')
        
        service = SearchService()
        metrics = service.get_search_performance(days=days, group_by=group_by)
        
        return Response(metrics)