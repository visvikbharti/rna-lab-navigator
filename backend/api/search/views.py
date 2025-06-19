from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, F, Prefetch
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import timedelta
import asyncio
import uuid
import hashlib
import json

from .models import (
    QuerySuggestion, QueryCompletion, SearchRankingProfile, 
    SearchAnalytics, SearchFacet, SavedSearch
)
from .services import QuerySuggestionService, SearchService
from .serializers import (
    QuerySuggestionSerializer, QueryCompletionSerializer,
    SearchRankingProfileSerializer, SearchAnalyticsSerializer
)
from ..serializers import DocumentSerializer
from ..rag.enhanced_rag import get_enhanced_rag_pipeline

class QuerySuggestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for query suggestions management.
    """
    queryset = QuerySuggestion.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['query_text', 'category']
    ordering_fields = ['usage_count', 'success_rate', 'last_used']
    ordering = ['-usage_count']
    
    def get_queryset(self):
        """Optimize queryset with database optimization."""
        return super().get_queryset().select_related().prefetch_related()
    
    def get_serializer_class(self):
        return QuerySuggestionSerializer
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular query suggestions based on usage count."""
        # Create cache key based on parameters
        limit = request.query_params.get('limit', 10)
        category = request.query_params.get('category', None)
        cache_key = f"popular_queries:{limit}:{category}"
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response(cached_result)
        
        service = QuerySuggestionService()
        suggestions = service.get_popular_queries(limit=int(limit), category=category)
        
        # Store in cache
        cache.set(cache_key, suggestions, 300)  # 5 minutes
        return Response(suggestions)
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending query suggestions based on recent usage."""
        # Create cache key based on parameters
        limit = request.query_params.get('limit', 10)
        category = request.query_params.get('category', None)
        days = request.query_params.get('days', 7)
        cache_key = f"trending_queries:{limit}:{category}:{days}"
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response(cached_result)
        
        service = QuerySuggestionService()
        suggestions = service.get_trending_queries(
            limit=int(limit), 
            category=category,
            days=int(days)
        )
        
        # Store in cache
        cache.set(cache_key, suggestions, 300)  # 5 minutes
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
    
    def get_queryset(self):
        """Optimize queryset with select_related for creator."""
        return super().get_queryset().select_related('created_by')
    
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
        
        # Create cache key for frequent queries
        cache_key = None
        if query_text and not saved_search_id:
            # Create a deterministic cache key
            cache_data = {
                'query': query_text.lower().strip(),
                'doc_type': doc_type,
                'profile_id': profile_id,
                'limit': limit,
                'filters': filters,
                'facets': facets
            }
            cache_key = f"search:{hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                # Update analytics even for cached results
                if query_text:
                    QuerySuggestionService().record_query_usage(query_text, cached_result.get('results', []))
                return Response(cached_result)
        
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
            
            response_data = {
                'results': DocumentSerializer(results, many=True).data,
                'metadata': metadata
            }
            
            # Cache the result if we have a cache key
            if cache_key:
                cache.set(cache_key, response_data, 600)  # Cache for 10 minutes
            
            return Response(response_data)
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


class EnhancedRAGViewSet(viewsets.ViewSet):
    """
    ViewSet for enhanced conversational RAG with memory and reasoning.
    """
    
    def create(self, request):
        """
        Process a query with enhanced RAG pipeline.
        
        POST parameters:
        - query: The search query
        - session_id: (optional) Session ID for conversation memory
        - user_context: (optional) User context information
        """
        query = request.data.get('query', '')
        session_id = request.data.get('session_id', str(uuid.uuid4()))
        user_context = request.data.get('user_context', {})
        
        if not query:
            return Response(
                {"error": "Field 'query' is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get enhanced RAG pipeline
            enhanced_rag = get_enhanced_rag_pipeline()
            
            # Process query asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                enhanced_rag.process_query(query, session_id, user_context)
            )
            
            loop.close()
            
            return Response(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Enhanced RAG error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def autocomplete(self, request):
        """
        Get intelligent auto-complete suggestions.
        
        POST parameters:
        - partial_query: The partial query to complete
        - session_id: Session ID for context-aware suggestions
        """
        partial_query = request.data.get('partial_query', '')
        session_id = request.data.get('session_id', '')
        
        if not partial_query:
            return Response(
                {"error": "Field 'partial_query' is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            enhanced_rag = get_enhanced_rag_pipeline()
            suggestions = enhanced_rag.get_autocomplete_suggestions(partial_query, session_id)
            
            return Response({
                'suggestions': suggestions
            })
            
        except Exception as e:
            return Response(
                {"error": f"Autocomplete error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def feedback(self, request):
        """
        Record feedback for enhanced RAG responses.
        
        POST parameters:
        - session_id: Session ID
        - turn_index: Index of the conversation turn
        - rating: 1-5 rating
        - helpful: Boolean indicating if response was helpful
        - issues: List of issues (optional)
        """
        session_id = request.data.get('session_id')
        turn_index = request.data.get('turn_index')
        rating = request.data.get('rating')
        helpful = request.data.get('helpful')
        issues = request.data.get('issues', [])
        
        if not all([session_id, turn_index is not None, rating]):
            return Response(
                {"error": "Fields 'session_id', 'turn_index', and 'rating' are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            enhanced_rag = get_enhanced_rag_pipeline()
            enhanced_rag.record_feedback(
                session_id,
                int(turn_index),
                {
                    'rating': rating,
                    'helpful': helpful,
                    'issues': issues
                }
            )
            
            return Response({"status": "feedback recorded"})
            
        except Exception as e:
            return Response(
                {"error": f"Feedback error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SavedSearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing saved searches.
    """
    
    def get_queryset(self):
        # Only return saved searches for the authenticated user
        user = self.request.user
        if user.is_authenticated:
            return SavedSearch.objects.filter(user=user).select_related(
                'ranking_profile', 'user'
            ).prefetch_related(
                'filters__created_by'
            ).order_by('-last_used')
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
    
    @method_decorator(cache_page(3600))  # Cache for 1 hour
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
        cache_key = f"search_performance:{days}:{group_by}"
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response(cached_result)
        
        service = SearchService()
        metrics = service.get_search_performance(days=days, group_by=group_by)
        
        # Store in cache
        cache.set(cache_key, metrics, 3600)  # 1 hour
        return Response(metrics)