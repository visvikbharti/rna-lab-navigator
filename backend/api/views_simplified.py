"""
Simplified version of views.py for the demo.
This file removes dependencies on external libraries like numpy and sentence_transformers.
"""

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status, filters
from rest_framework.decorators import permission_classes, action
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Sum, Count
import hashlib
import json
import time
import random

from .models import QueryHistory, Feedback, QueryCache, Figure, Document
from .serializers import (
    QuerySerializer, 
    QueryHistorySerializer, 
    FeedbackSerializer,
    QueryCacheSerializer,
    EvaluationSetSerializer,
    ReferenceQuestionSerializer,
    EvaluationRunSerializer,
    QuestionResultSerializer,
    FigureSerializer
)

class HealthCheckView(APIView):
    """
    Simple health check endpoint to verify API is operational.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            "status": "healthy",
            "time": timezone.now().isoformat(),
            "version": "1.0.0",
        })

class QueryView(APIView):
    """
    Primary endpoint for querying the RNA Lab Navigator.
    """
    
    def rerank_results(self, query, results):
        """Mock reranking function for demo purposes."""
        # In a real implementation, this would use a cross-encoder
        # Here we just add mock scores
        for idx, result in enumerate(results):
            # Add some randomness but keep original order roughly preserved
            result['score'] = max(0.1, min(0.99, 0.9 - (idx * 0.05) + (random.random() * 0.1)))
        
        # Sort by score
        return sorted(results, key=lambda x: x.get('score', 0), reverse=True)
    
    def build_prompt(self, query, results):
        """Build a prompt for the LLM with the query and retrieved content."""
        prompt = "Answer only from the provided sources; if unsure, say 'I don't know.'\n\n"
        prompt += f"Question: {query}\n\n"
        prompt += "Sources:\n\n"
        
        for i, result in enumerate(results[:5]):  # Use top 5 results
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            source = metadata.get('title', f"Source {i+1}")
            
            prompt += f"[{i+1}] {source}\n{content}\n\n"
            
        return prompt
    
    def extract_sources(self, results):
        """Extract source information from results for citation."""
        sources = []
        for i, result in enumerate(results[:5]):  # Use top 5 results
            metadata = result.get('metadata', {})
            sources.append({
                'id': i+1,
                'title': metadata.get('title', f"Source {i+1}"),
                'doc_type': metadata.get('doc_type', 'unknown'),
                'year': metadata.get('year', ''),
                'author': metadata.get('author', ''),
                'page': metadata.get('page', None)
            })
        return sources
    
    def select_model(self, query, results):
        """Select the appropriate model based on query complexity."""
        # For demo, just return the default model
        return settings.OPENAI_MODEL
    
    def calculate_confidence_score(self, answer, results):
        """Calculate a confidence score for the answer based on retrieved results."""
        # Mock implementation - would normally be based on result scores and answer quality
        if not results:
            return 0.1
            
        # Average of top result scores with some randomness
        top_scores = [r.get('score', 0) for r in results[:3]]
        if not top_scores:
            return 0.3
            
        return sum(top_scores) / len(top_scores) * (0.9 + random.random() * 0.1)
    
    def post(self, request):
        """Process a query and return an answer with sources."""
        serializer = QuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query_text = serializer.validated_data['query']
        doc_type = serializer.validated_data.get('doc_type', None)
        # Normalize doc_type - treat empty string as 'all'
        if not doc_type or doc_type == '':
            doc_type = 'all'
        use_cache = serializer.validated_data.get('use_cache', True)
        
        # Check cache if enabled
        if use_cache:
            # Generate a hash for the query
            query_hash = hashlib.md5(query_text.encode()).hexdigest()
            try:
                cached_response = QueryCache.objects.get(query_hash=query_hash)
                # Update hit count and access time
                cached_response.hit_count += 1
                cached_response.last_accessed = timezone.now()
                cached_response.save()
                
                # Return cached result
                return Response({
                    'query': query_text,
                    'answer': cached_response.answer,
                    'sources': json.loads(cached_response.sources),
                    'confidence_score': cached_response.confidence_score,
                    'from_cache': True,
                    'processing_time': 0.1  # Minimal time for cache hit
                })
            except QueryCache.DoesNotExist:
                # Not in cache, continue with query processing
                pass
        
        # DEMO: Mock retrieval and answer generation
        start_time = time.time()
        
        # Mock results with some dummy content
        mock_results = [
            {
                'content': 'RNA biology involves the study of RNA molecules and their functions in cellular processes.',
                'metadata': {
                    'title': 'RNA Biology Fundamentals',
                    'doc_type': 'paper',
                    'year': '2023',
                    'author': 'Sharma et al.'
                }
            },
            {
                'content': 'PCR protocols require careful temperature control and primer design.',
                'metadata': {
                    'title': 'PCR Protocol Guide',
                    'doc_type': 'protocol',
                    'year': '2022',
                    'author': 'Kumar et al.'
                }
            },
            {
                'content': 'CRISPR technologies have revolutionized gene editing capabilities.',
                'metadata': {
                    'title': 'CRISPR Applications',
                    'doc_type': 'paper',
                    'year': '2024',
                    'author': 'Chakraborty et al.'
                }
            }
        ]
        
        # Rerank results
        reranked_results = self.rerank_results(query_text, mock_results)
        
        # Build prompt and generate answer
        prompt = self.build_prompt(query_text, reranked_results)
        
        # Use real RAG pipeline
        from api.search.real_rag import perform_rag_query
        
        try:
            rag_result = perform_rag_query(query_text, doc_type)
            answer = rag_result['answer']
            sources = rag_result['sources']
            search_results = rag_result['search_results']  # Include search results with snippets
            confidence_score = rag_result['confidence_score']
        except Exception as e:
            print(f"RAG pipeline error: {e}")
            # Mock LLM response as fallback
            answer = f"I apologize, but I'm having trouble accessing the document database. Please try again later."
            sources = self.extract_sources(reranked_results)
            search_results = []  # Empty search results for fallback
            confidence_score = 0.1
        
        # Sources and confidence already set by RAG pipeline or fallback
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Store query in history
        query_history = QueryHistory.objects.create(
            query_text=query_text,
            answer=answer,
            sources=json.dumps(sources),
            confidence_score=confidence_score,
            processing_time=processing_time,
            doc_type=doc_type or 'all'
        )
        
        # Store in cache if good confidence
        if confidence_score >= 0.45 and use_cache:
            query_hash = hashlib.md5(query_text.encode()).hexdigest()
            QueryCache.objects.create(
                query_text=query_text,
                query_hash=query_hash,
                answer=answer,
                sources=json.dumps(sources),
                confidence_score=confidence_score,
                doc_type=doc_type or 'all'
            )
        
        # Return response
        return Response({
            'query': query_text,
            'answer': answer,
            'sources': sources,
            'search_results': search_results,  # Include search results with snippets
            'confidence_score': confidence_score,
            'from_cache': False,
            'processing_time': processing_time
        })

class TestRAGView(APIView):
    """Debug endpoint to test RAG functionality."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        from api.search.real_rag import vector_store, perform_rag_query
        
        try:
            vector_count = len(vector_store.vectors)
            if vector_count == 0:
                return Response({
                    "status": "error",
                    "message": "Vector store is empty",
                    "vector_count": vector_count
                })
            
            # Test RAG query
            result = perform_rag_query("what is this thesis about", "all")
            
            return Response({
                "status": "success",
                "vector_count": vector_count,
                "test_query": "what is this thesis about",
                "answer_preview": result['answer'][:100] + "...",
                "confidence": result['confidence_score'],
                "sources": len(result['sources'])
            })
        except Exception as e:
            import traceback
            return Response({
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            })

class QueryHistoryViewSet(ReadOnlyModelViewSet):
    """ViewSet for query history."""
    queryset = QueryHistory.objects.all().order_by('-created_at')
    serializer_class = QueryHistorySerializer
    filterset_fields = ['doc_type']
    search_fields = ['query_text']

class FeedbackViewSet(ModelViewSet):
    """ViewSet for user feedback on answers."""
    queryset = Feedback.objects.all().order_by('-created_at')
    serializer_class = FeedbackSerializer
    
    def create(self, request, *args, **kwargs):
        # Add query_history to the request data
        data = request.data.copy()
        
        # Ensure query_history_id is provided
        if 'query_history_id' not in data:
            return Response(
                {"error": "query_history_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create feedback
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class QueryCacheView(APIView):
    """API endpoint for managing query cache."""
    
    def get(self, request):
        """Get cache statistics."""
        cache_count = QueryCache.objects.count()
        
        # Get metrics
        avg_confidence = QueryCache.objects.aggregate(Avg('confidence_score'))
        hit_counts = QueryCache.objects.aggregate(Sum('hit_count'), Avg('hit_count'))
        
        # Get top queries
        top_queries = QueryCache.objects.order_by('-hit_count')[:10]
        top_queries_data = QueryCacheSerializer(top_queries, many=True).data
        
        # Get doc_type distribution
        doc_types = QueryCache.objects.values('doc_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'cache_size': cache_count,
            'metrics': {
                'avg_confidence': avg_confidence.get('confidence_score__avg', 0),
                'total_hits': hit_counts.get('hit_count__sum', 0),
                'avg_hits': hit_counts.get('hit_count__avg', 0),
            },
            'top_queries': top_queries_data,
            'doc_type_distribution': list(doc_types)
        })
    
    def delete(self, request):
        """Clear the entire cache or specific entries."""
        query_hash = request.query_params.get('query_hash', None)
        
        if query_hash:
            # Delete specific cache entry
            try:
                cache_entry = QueryCache.objects.get(query_hash=query_hash)
                cache_entry.delete()
                return Response({
                    "message": f"Cache entry for {cache_entry.query_text} deleted successfully"
                })
            except QueryCache.DoesNotExist:
                return Response({
                    "error": "Cache entry not found"
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Delete all cache entries
            count = QueryCache.objects.count()
            QueryCache.objects.all().delete()
            return Response({
                "message": f"Query cache cleared ({count} entries deleted)"
            })

class FigureViewSet(ReadOnlyModelViewSet):
    """ViewSet for figures extracted from documents."""
    queryset = Figure.objects.all().order_by('-created_at')
    serializer_class = FigureSerializer
    filterset_fields = ['document', 'figure_type']
    search_fields = ['caption']

class DocumentPreviewView(APIView):
    """API endpoint for document preview."""
    
    def get(self, request, document_id):
        """Get a preview of a document."""
        try:
            # Get the actual document from database
            document = Document.objects.get(id=document_id)
            
            # Get content from vector store
            from api.search.real_rag import vector_store
            content_chunks = []
            for metadata in vector_store.metadata:
                if metadata['document_id'] == int(document_id):
                    content_chunks.append(metadata['text'])
            
            # Combine chunks for preview (limit to first 1000 chars)
            combined_content = ' '.join(content_chunks)
            preview_text = combined_content[:1000] + "..." if len(combined_content) > 1000 else combined_content
            
            return Response({
                'document_id': document_id,
                'title': document.title,
                'author': document.author,
                'year': document.year,
                'doc_type': document.doc_type,
                'preview': preview_text or "No content available for preview.",
                'created_at': document.created_at.isoformat(),
                'total_chunks': len(content_chunks)
            })
            
        except Document.DoesNotExist:
            return Response({
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error loading document: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)