from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status, filters
from rest_framework.decorators import permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

# Import evaluation views
from .views_evaluation import (
    EvaluationSetViewSet,
    ReferenceQuestionViewSet,
    EvaluationRunViewSet,
    QuestionResultViewSet,
    TriggerEvaluationView,
    EvaluationReportView
)
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Sum, Count
import numpy as np
import hashlib
import json
from sentence_transformers import CrossEncoder
from .offline import get_llm_client, get_cross_encoder, is_offline_mode

from .models import QueryHistory, Feedback, QueryCache, Figure
from .serializers import (
    QuerySerializer, 
    QueryHistorySerializer, 
    FeedbackSerializer,
    FeedbackCreateSerializer,
    QueryCacheSerializer,
    FigureSerializer
)
from .ingestion.embeddings_utils import search_weaviate
from .analytics.hooks import measure_query_time, measure_llm_time, log_query
from .analytics.collectors import ActivityCollector, MetricsCollector, AuditCollector


@permission_classes([AllowAny])
class HealthCheckView(APIView):
    """
    Simple health check endpoint to verify API is up and running.
    """
    
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


@permission_classes([AllowAny])
class QueryView(APIView):
    """
    RAG endpoint for querying the vector store and generating answers.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load cross-encoder model for reranking
        try:
            # First try to use the enhanced cross-encoder reranking
            try:
                from .search.reranking import get_cross_encoder
                self.cross_encoder = get_cross_encoder()
            except (ImportError, Exception) as e:
                # Fall back to existing cross-encoder if enhanced one is not available
                self.cross_encoder = get_cross_encoder()
        except Exception as e:
            print(f"Warning: Could not load cross-encoder: {e}")
            self.cross_encoder = None
            
    def check_query_cache(self, query, doc_type=""):
        """
        Check if the query is in the cache and return the cached response if found.
        Updates the hit count and last_accessed time if cache hit.
        
        Args:
            query (str): The user's query
            doc_type (str): Optional document type filter
            
        Returns:
            dict: Cached response or None if no cache hit
        """
        # Create a hash of the query + doc_type for efficient lookup
        query_key = f"{query.lower().strip()}_{doc_type}"
        query_hash = hashlib.sha256(query_key.encode()).hexdigest()
        
        try:
            # Look for the query in cache
            cached_query = QueryCache.objects.get(query_hash=query_hash)
            
            # Update cache metadata
            cached_query.hit_count += 1
            cached_query.last_accessed = timezone.now()
            cached_query.save()
            
            # Return the cached response
            return {
                "answer": cached_query.answer,
                "sources": cached_query.sources,
                "confidence_score": cached_query.confidence_score,
                "status": "success" if cached_query.confidence_score >= 0.45 else "low_confidence",
                "cache_hit": True
            }
        except QueryCache.DoesNotExist:
            # No cache hit
            return None
        except Exception as e:
            print(f"Error checking query cache: {e}")
            return None
            
    def save_to_cache(self, query, doc_type, answer, sources, confidence_score):
        """
        Save a query response to the cache for future use.
        
        Args:
            query (str): The user's query
            doc_type (str): Document type filter
            answer (str): Generated answer
            sources (list): Source information
            confidence_score (float): Confidence score
            
        Returns:
            bool: True if successfully cached, False otherwise
        """
        try:
            # Create a hash of the query + doc_type
            query_key = f"{query.lower().strip()}_{doc_type}"
            query_hash = hashlib.sha256(query_key.encode()).hexdigest()
            
            # Save to cache
            QueryCache.objects.create(
                query_hash=query_hash,
                query_text=query,
                doc_type=doc_type,
                answer=answer,
                sources=sources,
                confidence_score=confidence_score
            )
            return True
        except Exception as e:
            print(f"Error saving to query cache: {e}")
            return False
            
    def select_model(self, query, results, tier="default"):
        """
        Select the appropriate model based on query complexity and tier.
        
        Args:
            query (str): The user's query
            results (list): Retrieved results
            tier (str): Model tier preference
            
        Returns:
            str: The selected model ID
        """
        # Get model configuration
        model_config = getattr(settings, 'MODEL_TIERS', {})
        if not model_config:
            # Default configuration if not in settings
            model_config = {
                'small': 'gpt-3.5-turbo',
                'default': settings.OPENAI_MODEL,
                'large': 'gpt-4o'
            }
        
        # Check if tier exists in config
        if tier in model_config:
            return model_config[tier]
        
        # Measure query complexity (simple heuristic)
        query_complexity = self.measure_query_complexity(query, results)
        
        # Route based on complexity
        if query_complexity < 0.3:
            return model_config.get('small', 'gpt-3.5-turbo')
        elif query_complexity < 0.7:
            return model_config.get('default', settings.OPENAI_MODEL)
        else:
            return model_config.get('large', 'gpt-4o')
    
    def measure_query_complexity(self, query, results):
        """
        Measure the complexity of a query to determine appropriate model.
        
        Args:
            query (str): The user's query
            results (list): Retrieved results
            
        Returns:
            float: Complexity score (0-1), higher is more complex
        """
        # Simple heuristics for complexity
        complexity = 0.0
        
        # 1. Query length
        words = query.split()
        if len(words) > 20:
            complexity += 0.3
        elif len(words) > 10:
            complexity += 0.15
            
        # 2. Check for specific complexity indicators
        complexity_terms = [
            'compare', 'difference', 'explain', 'analyze', 'synthesize',
            'relationship', 'mechanism', 'pathway', 'protocol', 'method',
            'versus', 'pros and cons', 'advantages', 'disadvantages',
            'figure', 'table', 'image', 'graph', 'diagram', 'hypothetical'
        ]
        
        matched_terms = 0
        for term in complexity_terms:
            if term.lower() in query.lower():
                matched_terms += 1
                
        if matched_terms >= 3:
            complexity += 0.4
        elif matched_terms >= 1:
            complexity += 0.2
            
        # 3. Retrieved document complexity
        if results:
            content_length = sum(len(r.get('content', '')) for r in results[:3])
            if content_length > 3000:
                complexity += 0.3
            elif content_length > 1500:
                complexity += 0.15
                
        # Ensure the score is between 0 and 1
        return min(1.0, complexity)
    
    @measure_query_time(query_type="reranking")
    def rerank_results(self, query, results):
        """
        Rerank retrieved results using a cross-encoder model.
        
        Args:
            query (str): The user's query
            results (list): The results from the vector search
            
        Returns:
            list: Reranked results with scores
        """
        if not results:
            return results
            
        # Use the new enhanced cross-encoder reranking
        try:
            from .search.reranking import rerank_search_results
            
            # Apply cross-encoder reranking
            reranked_results, _ = rerank_search_results(
                query_text=query,
                results=results,
                top_k=None  # Don't limit results, we'll still return all of them
            )
            
            # If reranking succeeds, return the reranked results
            if reranked_results:
                # Ensure each result has a relevance_score for compatibility
                for result in reranked_results:
                    if "rerank_score" in result and "relevance_score" not in result:
                        result["relevance_score"] = result["rerank_score"]
                return reranked_results
        except ImportError:
            # Fall back to old method if new reranking module is not available
            pass
        except Exception as e:
            print(f"Error using enhanced reranking: {e}")
            # Fall back to old method
            pass
            
        # Fall back to old reranking method if enhanced reranking fails
        if not self.cross_encoder:
            return results
            
        # Prepare pairs for cross-encoder
        pairs = []
        for result in results:
            if "content" in result:
                text = result["content"]
            elif "caption" in result:
                text = result["caption"]
            else:
                text = ""
            pairs.append((query, text))
        
        # Get relevance scores
        scores = self.cross_encoder.predict(pairs)
        
        # Attach scores to results
        for i, result in enumerate(results):
            result["relevance_score"] = float(scores[i])
        
        # Sort by relevance score in descending order
        reranked_results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
        
        return reranked_results
    
    def build_prompt(self, query, results, max_results=3):
        """
        Build a prompt for the LLM with the query and retrieved context.
        
        Args:
            query (str): The user's query
            results (list): The reranked results
            max_results (int): Maximum number of results to include in the prompt
            
        Returns:
            str: Prompt for the LLM
        """
        # Try to use enhanced RAG if available
        try:
            from .rag.enhanced_rag import enhance_rag_context
            
            # Apply RAG enhancements to results
            enhanced_results = enhance_rag_context(
                query=query,
                chunks=results,
                max_context_chunks=max_results
            )
            
            # If successful, use the enhanced results
            if enhanced_results:
                top_results = enhanced_results[:max_results]
            else:
                # Fallback to basic top N results
                top_results = results[:max_results]
        except ImportError:
            # If enhanced RAG module is not available, use regular top results
            top_results = results[:max_results]
        except Exception as e:
            print(f"Error applying RAG enhancements: {e}")
            # Fallback to basic top N results
            top_results = results[:max_results]
        
        # Golden rule #2: Must start with specific instruction
        prompt = "Answer only from the provided sources; if unsure, say 'I don't know.'\n\n"
        
        # Add the query
        prompt += f"Query: {query}\n\n"
        
        # Add the sources
        prompt += "Sources:\n"
        
        for i, result in enumerate(top_results):
            # Check if this is a figure or a document
            if result.get('result_type') == 'figure' or 'figure_id' in result:
                # This is a figure result
                source_info = f"{result.get('title', 'Untitled')} ({result.get('doc_type', 'unknown')})"
                if result.get('author'):
                    source_info += f", by {result['author']}"
                
                figure_type = result.get('figure_type', 'Figure').capitalize()
                page_num = f"p.{result.get('page_number')}" if result.get('page_number') else ""
                
                prompt += f"[{i+1}] {source_info} - {figure_type} {page_num}\n"
                prompt += f"Caption: {result.get('caption', 'No caption available')}\n\n"
                
                # Include figure reference ID for the answer
                prompt += f"Figure reference ID: {result.get('figure_id', 'unknown')}\n\n"
                
            else:
                # This is a regular document result
                
                # Check if there's a pre-built citation from enhanced RAG
                if 'citation' in result:
                    source_info = result['citation']
                else:
                    # Build the citation information
                    source_info = f"{result.get('title', 'Untitled')} ({result.get('doc_type', 'unknown')})"
                    if result.get('author'):
                        source_info += f", by {result['author']}"
                    if result.get('chapter'):
                        source_info += f", Chapter {result['chapter']}"
                
                prompt += f"[{i+1}] {source_info}\n"
                prompt += f"{result['content']}\n\n"
        
        # Include instructions for figure references
        prompt += "Your answer should cite the sources using [1], [2], etc. notation. If a relevant figure is available, mention it using its figure reference ID. If the sources don't contain the information needed, say 'I don't know.'"
        
        return prompt
    
    def calculate_confidence_score(self, answer, results, max_results=3):
        """
        Calculate a confidence score for the answer.
        
        Args:
            answer (str): The generated answer
            results (list): The retrieved results
            max_results (int): The number of top results used
            
        Returns:
            float: Confidence score between 0 and 1
        """
        # Check if there are results
        if not results:
            return 0.0
        
        # Take the top N results
        top_results = results[:max_results]
        
        # Get relevance scores if available
        relevance_scores = [r.get("relevance_score", 0.5) for r in top_results]
        avg_relevance = np.mean(relevance_scores) if relevance_scores else 0.5
        
        # Check for source citations [1], [2], etc.
        citation_pattern = r'\[\d+\]'
        import re
        citations = re.findall(citation_pattern, answer)
        has_citations = len(citations) > 0
        
        # Check for "I don't know" response
        has_idk = "i don't know" in answer.lower()
        
        # Calculate confidence
        if has_idk:
            # If the system says it doesn't know, it's being honest but not helpful
            confidence = 0.2
        elif not has_citations:
            # No citations is bad (per golden rule #3)
            confidence = 0.3
        else:
            # Base confidence on relevance of retrieved documents
            confidence = min(0.9, avg_relevance)
            
            # Boost confidence if we have multiple citations
            citation_boost = min(0.1, len(set(citations)) * 0.03)
            confidence += citation_boost
        
        return confidence
    
    def extract_sources(self, results, max_results=3):
        """
        Extract source information from results.
        
        Args:
            results (list): The retrieved results
            max_results (int): Maximum number of results to include
            
        Returns:
            list: List of source information dictionaries
        """
        top_results = results[:max_results]
        sources = []
        figures = []
        
        for result in top_results:
            # Check if this is a figure or document
            if result.get('result_type') == 'figure' or 'figure_id' in result:
                # This is a figure
                figure = {
                    "figure_id": result.get("figure_id", "unknown"),
                    "figure_type": result.get("figure_type", "image"),
                    "caption": result.get("caption", ""),
                    "doc_title": result.get("title", "Untitled"),
                    "doc_type": result.get("doc_type", "unknown"),
                    "page_number": result.get("page_number"),
                }
                
                # Add figure API URL if available
                if 'figure_id' in result:
                    figure_id = result.get("figure_id")
                    # We'll get the full URL from the frontend
                    figure["api_path"] = f"/api/figures/{figure_id}/"
                
                figures.append(figure)
            else:
                # This is a regular document
                source = {
                    "title": result.get("title", "Untitled"),
                    "doc_type": result.get("doc_type", "unknown"),
                }
                
                if result.get("author"):
                    source["author"] = result["author"]
                
                if result.get("year"):
                    source["year"] = result["year"]
                
                if result.get("chapter"):
                    source["chapter"] = result["chapter"]
                
                sources.append(source)
        
        # Return combined object with both sources and figures
        return {
            "documents": sources,
            "figures": figures
        }
    
    @log_query
    def post(self, request):
        """
        Process a query and return a generated answer with sources.
        Supports both standard response and streaming response.
        """
        serializer = QuerySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data["query"]
        doc_type = serializer.validated_data.get("doc_type", "")
        use_hybrid = serializer.validated_data.get("use_hybrid", True)
        hybrid_alpha = serializer.validated_data.get("hybrid_alpha", 0.75)
        use_cache = serializer.validated_data.get("use_cache", True)
        model_tier = serializer.validated_data.get("model_tier", "default")
        stream = request.query_params.get('stream', 'false').lower() == 'true'
        
        # Check cache first if enabled
        if use_cache and not stream:
            cache_hit = self.check_query_cache(query, doc_type)
            if cache_hit:
                return Response(cache_hit, status=status.HTTP_200_OK)
        
        # Search Weaviate for relevant documents
        results = search_weaviate(
            query, 
            doc_type=doc_type, 
            limit=10,
            use_hybrid=use_hybrid,
            alpha=hybrid_alpha,
            include_figures=True
        )
        
        # Rerank the results
        reranked_results = self.rerank_results(query, results)
        
        # Build a prompt for the LLM
        prompt = self.build_prompt(query, reranked_results)
        
        # Extract source information for the response
        sources = self.extract_sources(reranked_results)
        
        # Select model based on tier and query complexity
        selected_model = self.select_model(query, reranked_results, model_tier)
        
        try:
            # Set up LLM client (OpenAI online or local offline)
            client = get_llm_client()
            
            if stream:
                # Streaming response
                from django.http import StreamingHttpResponse
                import json
                
                def event_stream():
                    """Generate SSE events from streaming response"""
                    # Create consistent params for both online and offline modes
                    messages = [
                        {"role": "system", "content": "You are a helpful assistant for RNA biology lab. Provide accurate, cited answers based only on the provided sources."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    # Handle different client interfaces for online/offline
                    # Start timing LLM generation
                    llm_start_time = time.time()
                    
                    if is_offline_mode():
                        response = client.chat().completions().create(
                            model=selected_model,
                            messages=messages,
                            temperature=0.2,
                            max_tokens=1000,
                            stream=True
                        )
                    else:
                        response = client.chat.completions.create(
                            model=selected_model,
                            messages=messages,
                            temperature=0.2,
                            max_tokens=1000,
                            top_p=1.0,
                            stream=True  # Enable streaming
                        )
                        
                    # Metrics will be recorded after streaming completes
                    
                    full_answer = ""
                    
                    # Yield initial metadata as SSE
                    metadata = {
                        "type": "metadata",
                        "sources": sources['documents'],
                        "figures": sources['figures']
                    }
                    yield f"data: {json.dumps(metadata)}\n\n"
                    
                    # Stream the content chunks
                    if is_offline_mode():
                        # Handle local model streaming (may be simulated)
                        for chunk in response:
                            if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta'):
                                content = chunk.choices[0].delta.content
                                if content:
                                    full_answer += content
                                    data = {
                                        "type": "content",
                                        "content": content
                                    }
                                    yield f"data: {json.dumps(data)}\n\n"
                    else:
                        # Handle OpenAI streaming
                        for chunk in response:
                            if chunk.choices and chunk.choices[0].delta.content:
                                content = chunk.choices[0].delta.content
                                full_answer += content
                                data = {
                                    "type": "content",
                                    "content": content
                                }
                                yield f"data: {json.dumps(data)}\n\n"
                    
                    # Calculate confidence after we have the full answer
                    confidence_score = self.calculate_confidence_score(full_answer, reranked_results)
                    
                    # Drop answers with confidence < 0.45 (golden rule #3)
                    if confidence_score < 0.45:
                        status_value = "low_confidence"
                    else:
                        status_value = "success"
                    
                    # Record LLM metrics after streaming completes
                    llm_elapsed_ms = (time.time() - llm_start_time) * 1000
                    # Estimate token counts (approximation for streaming)
                    prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
                    completion_tokens = len(full_answer.split()) * 1.3  # Rough estimate
                    
                    MetricsCollector.record_llm_generation_time(
                        model=selected_model,
                        prompt_tokens=int(prompt_tokens),
                        completion_tokens=int(completion_tokens),
                        time_ms=llm_elapsed_ms,
                        metadata={
                            'streaming': True,
                            'confidence_score': confidence_score,
                            'status': status_value
                        }
                    )
                    
                    # Yield final event with status and confidence
                    final = {
                        "type": "final",
                        "confidence_score": confidence_score,
                        "status": status_value
                    }
                    yield f"data: {json.dumps(final)}\n\n"
                    
                    # Save the query to history
                    query_history = QueryHistory.objects.create(
                        query_text=query,
                        answer=full_answer,
                        confidence_score=confidence_score,
                        sources=sources['documents']  # Keep compatibility with existing model
                    )
                    
                    # Cache the response if it's good quality and caching is enabled
                    if use_cache and status_value == "success" and confidence_score >= 0.6:
                        self.save_to_cache(
                            query=query,
                            doc_type=doc_type,
                            answer=full_answer,
                            sources=sources['documents'],  # Keep compatibility with existing model
                            confidence_score=confidence_score
                        )
                    
                    # Update the final event to include query_id for feedback
                    final["query_id"] = query_history.id
                    final["model_used"] = selected_model
                
                # Return streaming response
                return StreamingHttpResponse(
                    event_stream(),
                    content_type='text/event-stream'
                )
            
            else:
                # Standard non-streaming response
                messages = [
                    {"role": "system", "content": "You are a helpful assistant for RNA biology lab. Provide accurate, cited answers based only on the provided sources."},
                    {"role": "user", "content": prompt}
                ]
                
                # Handle different client interfaces for online/offline
                # Start timing LLM generation
                llm_start_time = time.time()
                
                if is_offline_mode():
                    response = client.chat().completions().create(
                        model=selected_model,
                        messages=messages,
                        temperature=0.2,
                        max_tokens=1000
                    )
                    # Extract content from local model response
                    answer = response.choices[0].message.content
                else:
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=messages,
                        temperature=0.2,
                        max_tokens=1000,
                        top_p=1.0
                    )
                    # Extract content from OpenAI response
                    answer = response.choices[0].message.content
                
                # Calculate LLM metrics
                llm_elapsed_ms = (time.time() - llm_start_time) * 1000
                
                # Extract token counts if available
                prompt_tokens = 0
                completion_tokens = 0
                
                try:
                    if hasattr(response, 'usage'):
                        prompt_tokens = getattr(response.usage, 'prompt_tokens', 0)
                        completion_tokens = getattr(response.usage, 'completion_tokens', 0)
                    elif isinstance(response, dict) and 'usage' in response:
                        prompt_tokens = response['usage'].get('prompt_tokens', 0)
                        completion_tokens = response['usage'].get('completion_tokens', 0)
                except Exception:
                    # Fall back to approximation if proper token counts not available
                    prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
                    completion_tokens = len(answer.split()) * 1.3  # Rough estimate
                
                # Record LLM metrics
                MetricsCollector.record_llm_generation_time(
                    model=selected_model,
                    prompt_tokens=int(prompt_tokens) if prompt_tokens else 0,
                    completion_tokens=int(completion_tokens) if completion_tokens else 0,
                    time_ms=llm_elapsed_ms
                )
                
                # Calculate confidence score
                confidence_score = self.calculate_confidence_score(answer, reranked_results)
                
                # Drop answers with confidence < 0.45 (golden rule #3)
                if confidence_score < 0.45:
                    answer = "I don't have enough reliable information to answer that question confidently."
                    status_value = "low_confidence"
                else:
                    status_value = "success"
                
                # Save the query to history
                query_history = QueryHistory.objects.create(
                    query_text=query,
                    answer=answer,
                    confidence_score=confidence_score,
                    sources=sources['documents']  # Keep compatibility with existing model
                )
                
                # Cache the response if it's good quality and caching is enabled
                if use_cache and status_value == "success" and confidence_score >= 0.6:
                    self.save_to_cache(
                        query=query,
                        doc_type=doc_type,
                        answer=answer,
                        sources=sources['documents'],  # Keep compatibility with existing model
                        confidence_score=confidence_score
                    )
                
                # Return the response
                response_data = {
                    "answer": answer,
                    "sources": sources['documents'],
                    "figures": sources['figures'],
                    "confidence_score": confidence_score,
                    "status": status_value,
                    "query_id": query_history.id,  # Include for feedback
                    "model_used": selected_model
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"Error in query processing: {e}")
            return Response(
                {"error": "An error occurred while processing your query."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@permission_classes([AllowAny])
class FeedbackViewSet(ModelViewSet):
    """
    ViewSet for managing user feedback on answers.
    Provides CRUD operations for feedback records.
    """
    queryset = Feedback.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackCreateSerializer
        return FeedbackSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get feedback statistics - counts and averages for ratings.
        Useful for dashboards and model improvement tracking.
        """
        total_count = Feedback.objects.count()
        positive_count = Feedback.objects.filter(rating='thumbs_up').count()
        negative_count = Feedback.objects.filter(rating='thumbs_down').count()
        
        # Calculate average ratings for different aspects
        retrieval_avg = Feedback.objects.filter(
            retrieval_quality__isnull=False
        ).values_list('retrieval_quality', flat=True).aggregate(Avg('retrieval_quality'))
        
        relevance_avg = Feedback.objects.filter(
            answer_relevance__isnull=False
        ).values_list('answer_relevance', flat=True).aggregate(Avg('answer_relevance'))
        
        citation_avg = Feedback.objects.filter(
            citation_accuracy__isnull=False
        ).values_list('citation_accuracy', flat=True).aggregate(Avg('citation_accuracy'))
        
        # Recent trends (last 7 days)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        recent_positive = Feedback.objects.filter(
            rating='thumbs_up', 
            created_at__gte=week_ago
        ).count()
        
        recent_negative = Feedback.objects.filter(
            rating='thumbs_down', 
            created_at__gte=week_ago
        ).count()
        
        return Response({
            'total_feedback': total_count,
            'positive_feedback': positive_count,
            'negative_feedback': negative_count,
            'positive_ratio': positive_count / total_count if total_count > 0 else None,
            'retrieval_quality_avg': retrieval_avg.get('retrieval_quality__avg'),
            'answer_relevance_avg': relevance_avg.get('answer_relevance__avg'),
            'citation_accuracy_avg': citation_avg.get('citation_accuracy__avg'),
            'recent_positive': recent_positive,
            'recent_negative': recent_negative
        })
    
    @action(detail=False, methods=['get'])
    def common_issues(self, request):
        """
        Analyze feedback comments and specific_issues to identify common problems.
        """
        # Get all specific issues from JSON field
        all_issues = []
        feedbacks_with_issues = Feedback.objects.filter(
            specific_issues__isnull=False
        ).values_list('specific_issues', flat=True)
        
        for issues in feedbacks_with_issues:
            if issues:
                all_issues.extend(issues)
        
        # Count occurrences of each issue
        issue_counts = {}
        for issue in all_issues:
            if issue in issue_counts:
                issue_counts[issue] += 1
            else:
                issue_counts[issue] = 1
        
        # Sort by frequency
        sorted_issues = sorted(
            issue_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return Response({
            'common_issues': sorted_issues[:10],  # Top 10 issues
            'total_issues': len(all_issues)
        })


@permission_classes([AllowAny])
class QueryHistoryViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for read-only access to query history.
    Used for analytics and review of past queries.
    """
    queryset = QueryHistory.objects.all().order_by('-created_at')
    serializer_class = QueryHistorySerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics about queries - count, avg confidence, etc.
        """
        total_count = QueryHistory.objects.count()
        
        # Average confidence score
        avg_confidence = QueryHistory.objects.values_list(
            'confidence_score', flat=True
        ).aggregate(Avg('confidence_score'))
        
        # Count queries with low confidence
        low_confidence_count = QueryHistory.objects.filter(
            confidence_score__lt=0.45
        ).count()
        
        # Recent query volume (last 24 hours)
        day_ago = timezone.now() - timezone.timedelta(days=1)
        recent_count = QueryHistory.objects.filter(
            created_at__gte=day_ago
        ).count()
        
        return Response({
            'total_queries': total_count,
            'avg_confidence': avg_confidence.get('confidence_score__avg'),
            'low_confidence_count': low_confidence_count,
            'low_confidence_ratio': low_confidence_count / total_count if total_count > 0 else None,
            'recent_queries': recent_count
        })
    
    @action(detail=False, methods=['get'])
    def doc_type_breakdown(self, request):
        """
        Get breakdown of queries by document type.
        """
        # This requires parsing the sources JSON field to extract doc_types
        query_histories = QueryHistory.objects.all()
        doc_type_counts = {}
        
        for qh in query_histories:
            doc_types = set()
            
            # Extract unique doc_types from sources
            for source in qh.sources:
                if 'doc_type' in source:
                    doc_types.add(source['doc_type'])
            
            # Count each doc_type
            for doc_type in doc_types:
                if doc_type in doc_type_counts:
                    doc_type_counts[doc_type] += 1
                else:
                    doc_type_counts[doc_type] = 1
        
        return Response(doc_type_counts)


@permission_classes([AllowAny])
class QueryCacheView(APIView):
    """
    API for managing the query cache.
    Supports clearing and viewing cache statistics.
    """
    
    def get(self, request):
        """Get cache statistics"""
        total_entries = QueryCache.objects.count()
        total_hits = QueryCache.objects.aggregate(Sum('hit_count'))
        
        # Get most frequently accessed cache entries
        top_entries = QueryCache.objects.order_by('-hit_count')[:5]
        
        # Get least recently used entries
        lru_entries = QueryCache.objects.order_by('last_accessed')[:5]
        
        return Response({
            'total_entries': total_entries,
            'total_hits': total_hits.get('hit_count__sum'),
            'top_entries': QueryCacheSerializer(top_entries, many=True).data,
            'least_recently_used': QueryCacheSerializer(lru_entries, many=True).data
        })
    
    def delete(self, request):
        """Clear the entire cache or specific entries"""
        entry_id = request.query_params.get('id')
        
        if entry_id:
            # Delete specific entry
            try:
                entry = QueryCache.objects.get(id=entry_id)
                entry.delete()
                return Response({"message": f"Cache entry {entry_id} deleted"})
            except QueryCache.DoesNotExist:
                return Response(
                    {"error": f"Cache entry {entry_id} not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Clear entire cache
            count = QueryCache.objects.count()
            QueryCache.objects.all().delete()
            return Response({"message": f"{count} cache entries cleared"})


@permission_classes([AllowAny])
class FigureViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for read-only access to extracted figures from documents.
    Supports filtering by document, figure type, and search by caption.
    """
    queryset = Figure.objects.all().order_by('-created_at')
    serializer_class = FigureSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['document', 'figure_type', 'page_number']
    search_fields = ['caption']
    
    def get_serializer_context(self):
        """Add request to serializer context for file URL generation"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'])
    def by_document(self, request):
        """Get figures grouped by document"""
        # Get all documents with figures
        documents = set(Figure.objects.values_list('document', flat=True))
        
        result = {}
        for doc_id in documents:
            doc_figures = Figure.objects.filter(document_id=doc_id)
            doc_info = doc_figures.first().document
            result[doc_id] = {
                'document_title': doc_info.title,
                'document_type': doc_info.doc_type,
                'figure_count': doc_figures.count(),
                'figures': FigureSerializer(
                    doc_figures,
                    many=True,
                    context={'request': request}
                ).data
            }
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def search_by_content(self, request):
        """
        Search figures by their caption content using vector search.
        More advanced than the basic search field.
        """
        query = request.query_params.get('query', '')
        limit = int(request.query_params.get('limit', '5'))
        
        if not query:
            return Response(
                {"error": "Query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search figure captions in Weaviate
        try:
            results = search_weaviate(
                query, 
                collection="Figure",
                limit=limit
            )
            
            # Match results to actual Figure objects
            figure_ids = [r.get('figure_id') for r in results if 'figure_id' in r]
            figures = Figure.objects.filter(figure_id__in=figure_ids)
            
            return Response(
                FigureSerializer(
                    figures, 
                    many=True,
                    context={'request': request}
                ).data
            )
        except Exception as e:
            return Response(
                {"error": f"Error searching figures: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )