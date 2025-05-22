"""
Services for enhanced search functionality.
"""

import time
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Q, F, Count, Avg, ExpressionWrapper, FloatField
from django.db.models.functions import Length
from datetime import timedelta

from .reranking import rerank_search_results, rerank_chunks_for_rag

from ..models import QueryHistory, Feedback
from ..ingestion.embeddings_utils import search_weaviate, generate_embedding
from .models import (
    QuerySuggestion, 
    QueryCompletion, 
    SearchRankingProfile,
    SearchAnalytics,
    SearchFilter,
    SearchFacet,
    SavedSearch
)

logger = logging.getLogger(__name__)


class QuerySuggestionService:
    """
    Service for managing and generating query suggestions.
    """
    
    @staticmethod
    def get_popular_queries(limit: int = 5, doc_type: str = None) -> List[Dict]:
        """
        Get popular queries based on usage count.
        
        Args:
            limit (int): Number of suggestions to return
            doc_type (str, optional): Filter by document type
            
        Returns:
            List of query suggestion objects
        """
        query = QuerySuggestion.objects.filter(
            usage_count__gt=0
        ).order_by('-usage_count')
        
        if doc_type:
            query = query.filter(doc_type=doc_type)
        
        suggestions = query[:limit]
        
        return [
            {
                "id": str(s.id),
                "query": s.query_text,
                "category": s.category,
                "doc_type": s.doc_type,
                "usage_count": s.usage_count,
                "success_rate": s.success_count / s.usage_count if s.usage_count > 0 else 0,
                "is_featured": s.is_featured
            }
            for s in suggestions
        ]
    
    @staticmethod
    def get_trending_queries(limit: int = 5, doc_type: str = None) -> List[Dict]:
        """
        Get trending queries based on recent usage and success.
        
        Args:
            limit (int): Number of suggestions to return
            doc_type (str, optional): Filter by document type
            
        Returns:
            List of query suggestion objects
        """
        # Calculate trending score based on recent usage and success
        query = QuerySuggestion.objects.filter(
            recent_count__gt=0
        ).order_by('-trending_score', '-recent_count')
        
        if doc_type:
            query = query.filter(doc_type=doc_type)
        
        suggestions = query[:limit]
        
        return [
            {
                "id": str(s.id),
                "query": s.query_text,
                "category": s.category,
                "doc_type": s.doc_type,
                "recent_count": s.recent_count,
                "trending_score": s.trending_score,
                "success_rate": s.recent_success_count / s.recent_count if s.recent_count > 0 else 0,
                "is_featured": s.is_featured
            }
            for s in suggestions
        ]
    
    @staticmethod
    def get_featured_queries(limit: int = 5, doc_type: str = None) -> List[Dict]:
        """
        Get featured queries that are manually curated.
        
        Args:
            limit (int): Number of suggestions to return
            doc_type (str, optional): Filter by document type
            
        Returns:
            List of query suggestion objects
        """
        query = QuerySuggestion.objects.filter(
            is_featured=True
        ).order_by('-usage_count')
        
        if doc_type:
            query = query.filter(doc_type=doc_type)
        
        suggestions = query[:limit]
        
        return [
            {
                "id": str(s.id),
                "query": s.query_text,
                "category": s.category,
                "doc_type": s.doc_type,
                "usage_count": s.usage_count,
                "success_rate": s.success_count / s.usage_count if s.usage_count > 0 else 0,
                "is_featured": True
            }
            for s in suggestions
        ]
    
    @staticmethod
    def get_semantic_suggestions(query_text: str, limit: int = 5) -> List[Dict]:
        """
        Get semantically similar query suggestions.
        
        Args:
            query_text (str): Input query text
            limit (int): Number of suggestions to return
            
        Returns:
            List of query suggestion objects
        """
        # Get all query suggestions
        all_suggestions = QuerySuggestion.objects.all()
        
        if not all_suggestions.exists():
            return []
        
        # Generate embedding for input query
        query_embedding = generate_embedding(query_text)
        if not query_embedding:
            return []
        
        # Prepare to score each suggestion
        suggestions_with_scores = []
        
        for suggestion in all_suggestions:
            # Get existing embedding or generate new one
            # In a real implementation, you'd store embeddings with suggestions
            suggestion_embedding = generate_embedding(suggestion.query_text)
            
            if suggestion_embedding:
                # Calculate cosine similarity
                similarity = QuerySuggestionService._cosine_similarity(
                    query_embedding, suggestion_embedding
                )
                
                suggestions_with_scores.append({
                    "id": str(suggestion.id),
                    "query": suggestion.query_text,
                    "category": suggestion.category,
                    "doc_type": suggestion.doc_type,
                    "usage_count": suggestion.usage_count,
                    "similarity": similarity,
                    "is_featured": suggestion.is_featured
                })
        
        # Sort by similarity score
        suggestions_with_scores.sort(key=lambda x: x["similarity"], reverse=True)
        
        return suggestions_with_scores[:limit]
    
    @staticmethod
    def get_autocomplete_suggestions(prefix: str, limit: int = 5) -> List[str]:
        """
        Get autocomplete suggestions for a query prefix.
        
        Args:
            prefix (str): Query prefix to autocomplete
            limit (int): Number of suggestions to return
            
        Returns:
            List of completion strings
        """
        if not prefix or len(prefix) < 2:
            return []
        
        prefix = prefix.lower()
        
        # First try exact prefix matches
        completions = QueryCompletion.objects.filter(
            prefix=prefix
        ).order_by('-frequency')[:limit]
        
        if not completions.exists():
            # Try as a LIKE query
            completions = QueryCompletion.objects.filter(
                prefix__startswith=prefix
            ).order_by('-frequency')[:limit]
        
        # If still no results, try partial match on completion field
        if not completions.exists():
            completions = QueryCompletion.objects.filter(
                completion__icontains=prefix
            ).order_by('-frequency')[:limit]
        
        return [c.completion for c in completions]
    
    @staticmethod
    def record_query(query_text: str, confidence_score: float = None,
                    doc_type: str = None, is_successful: bool = None) -> None:
        """
        Record a query for suggestion purposes, updating existing suggestion or creating new one.
        
        Args:
            query_text (str): The query text
            confidence_score (float, optional): Confidence score of the answer
            doc_type (str, optional): Document type that was queried
            is_successful (bool, optional): Whether query was successful
        """
        query_text = query_text.strip()
        if not query_text:
            return
        
        # Check if suggestion already exists
        suggestion, created = QuerySuggestion.objects.get_or_create(
            query_text=query_text,
            defaults={
                "doc_type": doc_type or ""
            }
        )
        
        # Determine success based on confidence score if not provided
        if is_successful is None and confidence_score is not None:
            is_successful = confidence_score >= 0.6
        
        # Update usage counts
        suggestion.increment_usage(success=is_successful)
        
        # Update quality metrics
        if confidence_score is not None:
            suggestion.update_metrics(confidence_score=confidence_score)
        
        # Update completions for autocomplete
        QuerySuggestionService._update_query_completions(query_text, doc_type)
    
    @staticmethod
    def update_trending_scores() -> int:
        """
        Update trending scores for all query suggestions.
        This should be run periodically (e.g., daily).
        
        Returns:
            int: Number of suggestions updated
        """
        week_ago = timezone.now() - timedelta(days=7)
        
        # Get all valid suggestions
        suggestions = QuerySuggestion.objects.all()
        
        # Calculate recent metrics
        for suggestion in suggestions:
            # Get counts from the last 7 days
            recent_queries = QueryHistory.objects.filter(
                query_text=suggestion.query_text,
                created_at__gte=week_ago
            )
            recent_count = recent_queries.count()
            
            # Calculate success count for those with confidence ≥ 0.6
            recent_success_count = recent_queries.filter(
                confidence_score__gte=0.6
            ).count()
            
            # Update suggestion
            suggestion.recent_count = recent_count
            suggestion.recent_success_count = recent_success_count
            
            # Calculate trending score - a simple method is:
            # (recent_count / total_count) * success_rate * log(recent_count + 1)
            if recent_count > 0:
                import math
                
                # Normalize by total count
                recency_factor = (recent_count / suggestion.usage_count 
                              if suggestion.usage_count > 0 else 1.0)
                
                # Success rate of recent queries
                success_rate = (recent_success_count / recent_count)
                
                # Logarithmic volume factor
                volume_factor = math.log(recent_count + 1)
                
                # Combine factors
                suggestion.trending_score = recency_factor * success_rate * volume_factor
            else:
                suggestion.trending_score = 0.0
            
            suggestion.save()
        
        return suggestions.count()
    
    @staticmethod
    def update_suggestion_from_feedback(feedback: Feedback) -> None:
        """
        Update query suggestion based on user feedback.
        
        Args:
            feedback (Feedback): The feedback object
        """
        if not feedback.query_history:
            return
        
        query_text = feedback.query_history.query_text
        if not query_text:
            return
            
        # Get or create suggestion
        suggestion, created = QuerySuggestion.objects.get_or_create(
            query_text=query_text
        )
        
        # Convert thumbs up/down to numerical rating
        rating = None
        if feedback.rating == 'thumbs_up':
            rating = 1.0
        elif feedback.rating == 'thumbs_down':
            rating = 0.0
        elif feedback.rating == 'neutral':
            rating = 0.5
            
        # Update metrics
        if rating is not None:
            suggestion.update_metrics(feedback_rating=rating)
    
    @staticmethod
    def generate_suggestions_from_history(min_count: int = 2, limit: int = 100) -> int:
        """
        Generate query suggestions based on query history.
        
        Args:
            min_count (int): Minimum query count to create a suggestion
            limit (int): Maximum number of suggestions to create
            
        Returns:
            int: Number of suggestions created
        """
        # Get query counts from history
        query_counts = QueryHistory.objects.values('query_text').annotate(
            count=Count('id'),
            avg_confidence=Avg('confidence_score')
        ).filter(
            count__gte=min_count
        ).order_by('-count')[:limit]
        
        created_count = 0
        
        for item in query_counts:
            query_text = item['query_text']
            avg_confidence = item['avg_confidence'] or 0.0
            
            # Skip if suggestion already exists
            if QuerySuggestion.objects.filter(query_text=query_text).exists():
                continue
                
            # Get document types for this query
            doc_type_counts = {}
            for history in QueryHistory.objects.filter(query_text=query_text):
                for source in history.sources:
                    if 'doc_type' in source:
                        doc_type = source['doc_type']
                        doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
            
            # Find most common doc_type
            doc_type = ""
            if doc_type_counts:
                doc_type = max(doc_type_counts.items(), key=lambda x: x[1])[0]
                
            # Count successful queries (confidence >= 0.6)
            success_count = QueryHistory.objects.filter(
                query_text=query_text,
                confidence_score__gte=0.6
            ).count()
            
            # Create suggestion
            suggestion = QuerySuggestion.objects.create(
                query_text=query_text,
                doc_type=doc_type,
                usage_count=item['count'],
                success_count=success_count,
                avg_confidence=avg_confidence,
                is_curated=False
            )
            
            created_count += 1
            
            # Update completions
            QuerySuggestionService._update_query_completions(query_text, doc_type)
        
        return created_count
    
    @staticmethod
    def _update_query_completions(query_text: str, doc_type: str = None) -> None:
        """
        Update query completions based on a query.
        
        Args:
            query_text (str): The query text
            doc_type (str, optional): Document type
        """
        words = query_text.lower().split()
        
        # Add completions for various n-grams
        for n in range(1, min(4, len(words))):
            for i in range(len(words) - n + 1):
                prefix = " ".join(words[i:i+n])
                
                # Skip very short prefixes
                if len(prefix) < 3:
                    continue
                
                completion, created = QueryCompletion.objects.get_or_create(
                    prefix=prefix,
                    completion=query_text,
                    defaults={"doc_type": doc_type or ""}
                )
                
                if not created:
                    # Increment frequency
                    completion.frequency += 1
                    completion.save()
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            float: Similarity score between 0 and 1
        """
        import numpy as np
        
        if not vec1 or not vec2:
            return 0
            
        # Convert to numpy arrays for efficient computation
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
            
        return dot_product / (norm_vec1 * norm_vec2)


class SearchService:
    """
    Service for enhanced search functionality.
    """
    
    def __init__(self):
        """Initialize the search service."""
        pass
    
    def get_default_ranking_profile(self) -> SearchRankingProfile:
        """
        Get the default search ranking profile.
        If no default exists, create a new one.
        
        Returns:
            SearchRankingProfile: The default ranking profile
        """
        # Try to get existing default
        try:
            return SearchRankingProfile.objects.get(is_default=True)
        except SearchRankingProfile.DoesNotExist:
            # Create default profile
            return SearchRankingProfile.objects.create(
                name="Default Profile",
                description="System default ranking profile",
                use_hybrid=True,
                hybrid_alpha=0.75,
                use_reranking=True,
                include_figures=True,
                is_default=True
            )
    
    def get_ranking_profile(self, profile_id: str = None) -> SearchRankingProfile:
        """
        Get a search ranking profile by ID or the default.
        
        Args:
            profile_id (str, optional): Profile ID to retrieve
            
        Returns:
            SearchRankingProfile: The retrieved ranking profile
        """
        if profile_id:
            try:
                return SearchRankingProfile.objects.get(id=profile_id)
            except SearchRankingProfile.DoesNotExist:
                return self.get_default_ranking_profile()
        else:
            return self.get_default_ranking_profile()
    
    def enhanced_search(self, query_text: str, doc_type: str = None, 
                       profile_id: str = None, limit: int = None,
                       session_id: str = None, user = None,
                       filters: List[Dict] = None, facets: List[Dict] = None,
                       saved_search_id: str = None) -> Tuple[List[Dict], Dict]:
        """
        Perform an enhanced search with custom ranking, filters, and facets.
        
        Args:
            query_text (str): The query text
            doc_type (str, optional): Document type filter
            profile_id (str, optional): Ranking profile ID
            limit (int, optional): Maximum results to return
            session_id (str, optional): Session ID for analytics
            user: User object for analytics
            filters (List[Dict], optional): List of filter criteria to apply
            facets (List[Dict], optional): List of facet selections
            saved_search_id (str, optional): ID of a saved search to use
            
        Returns:
            Tuple of (results list, search metadata)
        """
        start_time = time.time()
        
        # If using a saved search, apply its parameters
        saved_search = None
        if saved_search_id:
            try:
                saved_search = SavedSearch.objects.get(id=saved_search_id)
                
                # Override parameters with saved search values if not explicitly provided
                if saved_search.query_text and not query_text:
                    query_text = saved_search.query_text
                    
                if saved_search.ranking_profile and not profile_id:
                    profile_id = str(saved_search.ranking_profile.id)
                    
                # Include saved filters and facets if not explicitly provided
                if not filters and saved_search.parameters.get('filters'):
                    filters = saved_search.parameters.get('filters')
                    
                if not facets and saved_search.parameters.get('facets'):
                    facets = saved_search.parameters.get('facets')
                    
                # Update usage statistics
                saved_search.usage_count += 1
                saved_search.last_used = timezone.now()
                saved_search.save(update_fields=['usage_count', 'last_used'])
            except SavedSearch.DoesNotExist:
                pass
        
        # Get ranking profile
        profile = self.get_ranking_profile(profile_id)
        
        # Update usage count for profile
        profile.increment_usage()
        
        # Override limit if specified
        if limit is None:
            limit = profile.results_limit
        
        # Search parameters
        use_hybrid = profile.use_hybrid
        hybrid_alpha = profile.hybrid_alpha
        include_figures = profile.include_figures
        
        # Record query for suggestions
        QuerySuggestionService.record_query(
            query_text=query_text,
            doc_type=doc_type
        )
        
        # Build advanced filter criteria for Weaviate
        weaviate_filters = self._build_weaviate_filters(filters, doc_type)
        
        # Perform the search
        search_start_time = time.time()
        results = search_weaviate(
            query_text=query_text,
            doc_type=doc_type if not weaviate_filters else None,  # Skip since it's in weaviate_filters
            limit=limit,
            use_hybrid=use_hybrid,
            alpha=hybrid_alpha,
            include_figures=include_figures,
            filters=weaviate_filters if weaviate_filters else None
        )
        search_time_ms = int((time.time() - search_start_time) * 1000)
        
        # Apply custom ranking if needed
        if profile.doc_type_weights or profile.recency_boost > 0:
            results = self._apply_custom_ranking(results, profile)
        
        # Apply cross-encoder reranking if enabled
        reranking_time_ms = 0
        if profile.use_reranking and len(results) > 1:
            reranked_results, reranking_time_ms = rerank_search_results(
                query_text=query_text,
                results=results,
                # Do not limit results here, we want to keep all and apply custom ranking
                top_k=None
            )
            
            # Combine original ranking with reranking scores
            if reranked_results and profile.reranking_factor > 0:
                # Blend original scores with reranking scores
                for result in reranked_results:
                    # Original score (from custom ranking)
                    orig_score = result.get('custom_score', 0.5)
                    # Reranking score
                    rerank_score = result.get('rerank_score', 0.5)
                    
                    # Combine scores with specified factor
                    # reranking_factor controls how much influence reranking has
                    factor = profile.reranking_factor
                    final_score = ((1 - factor) * orig_score) + (factor * rerank_score)
                    result['final_score'] = final_score
                
                # Sort by final score
                reranked_results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
                
                # Use the reranked results
                results = reranked_results
            
        # Get facet information from results
        facet_info = self._extract_facet_information(results, facets) if facets else {}
        
        # Extract metadata
        top_doc_types = []
        for result in results[:5]:  # Only look at top 5
            doc_type = result.get('doc_type')
            if doc_type and doc_type not in top_doc_types:
                top_doc_types.append(doc_type)
        
        # Log search analytics
        analytics = SearchAnalytics.objects.create(
            query_text=query_text,
            user=user,
            session_id=session_id or "",
            doc_type=doc_type or "",
            use_hybrid=use_hybrid,
            hybrid_alpha=hybrid_alpha,
            ranking_profile=profile,
            num_results=len(results),
            top_doc_types=top_doc_types,
            search_time_ms=search_time_ms,
            reranking_time_ms=reranking_time_ms if profile.use_reranking else None,
            applied_filters=filters or [],
            applied_facets=facets or [],
            saved_search=saved_search
        )
        
        total_time_ms = int((time.time() - start_time) * 1000)
        
        metadata = {
            "query": query_text,
            "doc_type": doc_type,
            "profile": {
                "id": str(profile.id),
                "name": profile.name,
                "use_hybrid": profile.use_hybrid,
                "hybrid_alpha": profile.hybrid_alpha,
                "use_reranking": profile.use_reranking,
                "reranking_factor": profile.reranking_factor
            },
            "result_count": len(results),
            "search_time_ms": search_time_ms,
            "reranking_time_ms": reranking_time_ms,
            "total_time_ms": total_time_ms,
            "analytics_id": str(analytics.id),
            "facets": facet_info,
            "saved_search_id": str(saved_search.id) if saved_search else None
        }
        
        return results, metadata
    
    def _apply_custom_ranking(self, results: List[Dict], 
                            profile: SearchRankingProfile) -> List[Dict]:
        """
        Apply custom ranking to search results.
        
        Args:
            results: Original search results
            profile: Ranking profile to apply
            
        Returns:
            Reranked results
        """
        for result in results:
            # Initialize score with original relevance
            base_score = result.get('relevance_score', 0.5)
            final_score = base_score
            
            # Apply document type weighting
            if profile.doc_type_weights and 'doc_type' in result:
                doc_type = result['doc_type']
                weight = profile.doc_type_weights.get(doc_type, 1.0)
                final_score *= weight
            
            # Apply recency boost if available (using created_at field if present)
            if profile.recency_boost > 0 and 'created_at' in result:
                import datetime
                created_at = result['created_at']
                
                # Convert string to datetime if needed
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.datetime.fromisoformat(created_at)
                    except (ValueError, TypeError):
                        created_at = None
                
                if created_at:
                    # Calculate days since creation
                    now = timezone.now()
                    if isinstance(created_at, datetime.date) and not isinstance(created_at, datetime.datetime):
                        created_at = datetime.datetime.combine(created_at, datetime.time())
                        
                    days_old = (now - created_at).days
                    
                    # Apply recency boost (more recent = higher score)
                    # Max age considered is 365 days
                    if days_old <= 365:
                        recency_factor = 1.0 - (days_old / 365) * profile.recency_boost
                        final_score *= recency_factor
            
            # Store final score
            result['custom_score'] = final_score
        
        # Sort by custom score
        results.sort(key=lambda x: x.get('custom_score', 0), reverse=True)
        
        return results
    
    def update_analytics_with_answer(self, analytics_id: str, 
                                   confidence_score: float,
                                   answer_time_ms: int,
                                   query_history_id = None) -> None:
        """
        Update search analytics with answer generation data.
        
        Args:
            analytics_id (str): Analytics ID to update
            confidence_score (float): Answer confidence score
            answer_time_ms (int): Time taken to generate answer
            query_history_id: ID of associated QueryHistory object
        """
        try:
            analytics = SearchAnalytics.objects.get(id=analytics_id)
            
            analytics.confidence_score = confidence_score
            analytics.answer_time_ms = answer_time_ms
            
            if query_history_id:
                try:
                    from django.db.models.fields.related import RelatedField
                    # Check if query_history expects a string ID or object
                    field = SearchAnalytics._meta.get_field('query_history')
                    if isinstance(field, RelatedField):
                        # It's a foreign key, so we need to get the actual object
                        analytics.query_history_id = query_history_id
                    else:
                        # It's likely a direct ID field
                        analytics.query_history = query_history_id
                except Exception as e:
                    logger.error(f"Error setting query_history: {str(e)}")
                    analytics.query_history_id = query_history_id
            
            analytics.save()
        except (SearchAnalytics.DoesNotExist, Exception) as e:
            logger.error(f"Error updating analytics with answer: {str(e)}")
    
    def update_analytics_with_user_interaction(self, analytics_id: str,
                                            result_selected: bool = None,
                                            time_to_first_click: int = None) -> None:
        """
        Update search analytics with user interaction data.
        
        Args:
            analytics_id (str): Analytics ID to update
            result_selected (bool, optional): Whether user selected a result
            time_to_first_click (int, optional): Time to first click in ms
        """
        try:
            analytics = SearchAnalytics.objects.get(id=analytics_id)
            
            if result_selected is not None:
                analytics.result_selected = result_selected
                
            if time_to_first_click is not None:
                analytics.time_to_first_click = time_to_first_click
                
            analytics.save()
        except (SearchAnalytics.DoesNotExist, Exception) as e:
            logger.error(f"Error updating analytics with user interaction: {str(e)}")
    
    def _build_weaviate_filters(self, filters: List[Dict], doc_type: str = None) -> Dict:
        """
        Build Weaviate filter criteria from filter definitions.
        
        Args:
            filters (List[Dict]): List of filter criteria
            doc_type (str, optional): Document type filter to include
            
        Returns:
            Dict: Weaviate filter object
        """
        if not filters and not doc_type:
            return None
            
        # Start with empty filter
        weaviate_filter = {"operator": "And", "operands": []}
        
        # Add doc_type filter if specified
        if doc_type:
            weaviate_filter["operands"].append({
                "path": ["doc_type"],
                "operator": "Equal",
                "valueString": doc_type
            })
        
        # Add filters from filter list
        if filters:
            for filter_item in filters:
                filter_type = filter_item.get("type")
                field = filter_item.get("field")
                
                if not field:
                    continue
                    
                if filter_type == "term":
                    # Term filter (exact match)
                    value = filter_item.get("value")
                    if value is not None:
                        weaviate_filter["operands"].append({
                            "path": [field],
                            "operator": "Equal",
                            "valueString": str(value)
                        })
                        
                elif filter_type == "range":
                    # Numerical range filter
                    min_value = filter_item.get("min")
                    max_value = filter_item.get("max")
                    
                    if min_value is not None:
                        weaviate_filter["operands"].append({
                            "path": [field],
                            "operator": "GreaterThanEqual",
                            "valueNumber": float(min_value)
                        })
                    
                    if max_value is not None:
                        weaviate_filter["operands"].append({
                            "path": [field],
                            "operator": "LessThanEqual",
                            "valueNumber": float(max_value)
                        })
                        
                elif filter_type == "date_range":
                    # Date range filter
                    start_date = filter_item.get("start")
                    end_date = filter_item.get("end")
                    
                    if start_date:
                        weaviate_filter["operands"].append({
                            "path": [field],
                            "operator": "GreaterThanEqual",
                            "valueDate": start_date
                        })
                    
                    if end_date:
                        weaviate_filter["operands"].append({
                            "path": [field],
                            "operator": "LessThanEqual",
                            "valueDate": end_date
                        })
                        
                elif filter_type == "multi_term":
                    # Multiple term filter (IN operator)
                    values = filter_item.get("values", [])
                    if values:
                        # Create OR clause for multiple values
                        or_clause = {"operator": "Or", "operands": []}
                        
                        for value in values:
                            or_clause["operands"].append({
                                "path": [field],
                                "operator": "Equal",
                                "valueString": str(value)
                            })
                            
                        weaviate_filter["operands"].append(or_clause)
                        
                elif filter_type == "exists":
                    # Field exists filter
                    weaviate_filter["operands"].append({
                        "path": [field],
                        "operator": "NotEqual",
                        "valueNull": None
                    })
                    
                elif filter_type == "text":
                    # Text contains filter
                    text = filter_item.get("text")
                    if text:
                        weaviate_filter["operands"].append({
                            "path": [field],
                            "operator": "Like",
                            "valueString": f"*{text}*"
                        })
        
        # If no operands, return None
        if not weaviate_filter["operands"]:
            return None
            
        return weaviate_filter
    
    def _extract_facet_information(self, results: List[Dict], facets: List[Dict]) -> Dict:
        """
        Extract facet information from search results.
        
        Args:
            results: List of search results
            facets: List of facet specifications
            
        Returns:
            Dict: Facet information including available values and counts
        """
        facet_info = {}
        
        # Get configured facets from database
        db_facets = {}
        for facet in SearchFacet.objects.filter(
            name__in=[f.get("name") for f in facets if "name" in f]
        ):
            db_facets[facet.name] = {
                "id": str(facet.id),
                "name": facet.name,
                "display_name": facet.display_name,
                "field_path": facet.field_path,
                "facet_type": facet.facet_type,
                "config": facet.config
            }
        
        # Process each requested facet
        for facet_spec in facets:
            facet_name = facet_spec.get("name")
            if not facet_name or facet_name not in db_facets:
                continue
                
            facet_config = db_facets[facet_name]
            field_path = facet_config.get("field_path")
            facet_type = facet_config.get("facet_type")
            
            if not field_path:
                continue
                
            # Different handling based on facet type
            if facet_type == "categorical":
                # Count occurrences of each value
                value_counts = {}
                for result in results:
                    value = result.get(field_path)
                    if value:
                        value_counts[value] = value_counts.get(value, 0) + 1
                
                # Sort by count, then value
                sorted_values = sorted(
                    [{"value": k, "count": v} for k, v in value_counts.items()],
                    key=lambda x: (-x["count"], x["value"])
                )
                
                facet_info[facet_name] = {
                    "type": "categorical",
                    "display_name": facet_config["display_name"],
                    "values": sorted_values
                }
                
            elif facet_type == "numerical":
                # Find min/max and create buckets
                values = [float(result.get(field_path)) for result in results 
                         if result.get(field_path) is not None]
                
                if values:
                    min_val = min(values)
                    max_val = max(values)
                    
                    # Create buckets (default to 5)
                    num_buckets = facet_config.get("config", {}).get("num_buckets", 5)
                    
                    # Calculate bucket size
                    bucket_size = (max_val - min_val) / num_buckets if max_val > min_val else 1
                    
                    # Initialize buckets
                    buckets = []
                    for i in range(num_buckets):
                        bucket_min = min_val + (i * bucket_size)
                        bucket_max = min_val + ((i + 1) * bucket_size)
                        
                        # Last bucket should include max
                        if i == num_buckets - 1:
                            bucket_max = max_val
                            
                        buckets.append({
                            "min": bucket_min,
                            "max": bucket_max,
                            "count": 0
                        })
                    
                    # Count values in each bucket
                    for value in values:
                        for bucket in buckets:
                            if bucket["min"] <= value <= bucket["max"]:
                                bucket["count"] += 1
                                break
                                
                    facet_info[facet_name] = {
                        "type": "numerical",
                        "display_name": facet_config["display_name"],
                        "min": min_val,
                        "max": max_val,
                        "buckets": buckets
                    }
                    
            elif facet_type == "temporal":
                # Find min/max dates and create buckets
                date_values = []
                for result in results:
                    date_str = result.get(field_path)
                    if date_str:
                        try:
                            from dateutil import parser
                            date_values.append(parser.parse(date_str))
                        except Exception:
                            pass
                
                if date_values:
                    min_date = min(date_values)
                    max_date = max(date_values)
                    
                    # Default to monthly buckets
                    facet_info[facet_name] = {
                        "type": "temporal",
                        "display_name": facet_config["display_name"],
                        "min_date": min_date.isoformat(),
                        "max_date": max_date.isoformat(),
                        "date_values": [d.isoformat() for d in date_values]
                    }
                    
            elif facet_type == "hierarchical":
                # For hierarchical facets, extract hierarchy levels
                hierarchy = {}
                for result in results:
                    value = result.get(field_path)
                    if value:
                        # Split by configured delimiter (default '/')
                        delimiter = facet_config.get("config", {}).get("delimiter", "/")
                        parts = value.split(delimiter)
                        
                        # Build hierarchy
                        current = hierarchy
                        for i, part in enumerate(parts):
                            if part not in current:
                                current[part] = {"count": 0, "children": {}}
                            
                            current[part]["count"] += 1
                            
                            # Navigate to next level
                            if i < len(parts) - 1:
                                current = current[part]["children"]
                                
                facet_info[facet_name] = {
                    "type": "hierarchical",
                    "display_name": facet_config["display_name"],
                    "hierarchy": hierarchy
                }
        
        return facet_info
    
    def get_available_facets(self) -> List[Dict]:
        """
        Get all available search facets.
        
        Returns:
            List of facet configuration dictionaries
        """
        facets = SearchFacet.objects.all().order_by('display_order', 'display_name')
        
        return [
            {
                "id": str(f.id),
                "name": f.name,
                "display_name": f.display_name,
                "facet_type": f.facet_type,
                "field_path": f.field_path,
                "is_default": f.is_default,
                "config": f.config
            }
            for f in facets
        ]
    
    def get_saved_searches(self, user) -> List[Dict]:
        """
        Get saved searches for a user.
        
        Args:
            user: The user to get saved searches for
            
        Returns:
            List of saved search dictionaries
        """
        if not user or not user.is_authenticated:
            return []
            
        saved_searches = SavedSearch.objects.filter(user=user).order_by('-last_used')
        
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "query_text": s.query_text,
                "created_at": s.created_at.isoformat(),
                "last_used": s.last_used.isoformat() if s.last_used else None,
                "usage_count": s.usage_count,
                "ranking_profile": str(s.ranking_profile.id) if s.ranking_profile else None,
                "parameters": s.parameters
            }
            for s in saved_searches
        ]
    
    def save_search(self, user, name: str, query_text: str = "", 
                  profile_id: str = None, filters: List[Dict] = None,
                  facets: List[Dict] = None, description: str = "") -> SavedSearch:
        """
        Save a search for later use.
        
        Args:
            user: The user saving the search
            name: Name for the saved search
            query_text: Query text for the search
            profile_id: ID of ranking profile to use
            filters: List of filter criteria
            facets: List of facet selections
            description: Description of the saved search
            
        Returns:
            SavedSearch: The created or updated saved search
        """
        if not user or not user.is_authenticated:
            raise ValueError("User must be authenticated to save searches")
            
        # Get ranking profile if specified
        profile = None
        if profile_id:
            try:
                profile = SearchRankingProfile.objects.get(id=profile_id)
            except SearchRankingProfile.DoesNotExist:
                pass
        
        # Create or update saved search
        saved_search, created = SavedSearch.objects.update_or_create(
            user=user,
            name=name,
            defaults={
                "query_text": query_text,
                "ranking_profile": profile,
                "description": description,
                "parameters": {
                    "filters": filters or [],
                    "facets": facets or []
                },
                "last_used": timezone.now()
            }
        )
        
        return saved_search
    
    def get_search_ranking_profiles(self) -> List[Dict]:
        """
        Get all search ranking profiles.
        
        Returns:
            List of ranking profile dictionaries
        """
        profiles = SearchRankingProfile.objects.all().order_by('-is_default', 'name')
        
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "is_default": p.is_default,
                "usage_count": p.usage_count,
                "settings": {
                    "use_hybrid": p.use_hybrid,
                    "hybrid_alpha": p.hybrid_alpha,
                    "use_reranking": p.use_reranking,
                    "include_figures": p.include_figures,
                    "recency_boost": p.recency_boost,
                    "doc_type_weights": p.doc_type_weights
                }
            }
            for p in profiles
        ]