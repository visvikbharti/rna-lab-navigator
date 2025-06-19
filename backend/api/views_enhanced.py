"""
Enhanced views using the new hybrid search RAG system.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils import timezone
import hashlib
import json
import time
import uuid

from .models import QueryHistory, QueryCache
from .serializers import QuerySerializer
from .search.enhanced_real_rag import get_enhanced_rag_system


@permission_classes([AllowAny])
class EnhancedQueryView(APIView):
    """
    Enhanced query endpoint using hybrid search and advanced PDF processing.
    """
    
    def post(self, request):
        """Process a query using the enhanced RAG system."""
        serializer = QuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query_text = serializer.validated_data['query']
        doc_type = serializer.validated_data.get('doc_type', 'all')
        use_cache = serializer.validated_data.get('use_cache', True)
        use_local_embeddings = serializer.validated_data.get('use_local_embeddings', False)
        
        # Normalize doc_type
        if not doc_type or doc_type == '':
            doc_type = 'all'
        
        # Check cache if enabled
        if use_cache:
            query_hash = hashlib.md5(f"{query_text}_{doc_type}".encode()).hexdigest()
            try:
                cached_response = QueryCache.objects.get(query_hash=query_hash)
                cached_response.hit_count += 1
                cached_response.last_accessed = timezone.now()
                cached_response.save()
                
                return Response({
                    'query': query_text,
                    'answer': cached_response.answer,
                    'sources': json.loads(cached_response.sources),
                    'confidence_score': cached_response.confidence_score,
                    'from_cache': True,
                    'processing_time': 0.1,
                    'search_metadata': {
                        'search_type': 'cached',
                        'result_count': len(json.loads(cached_response.sources))
                    }
                })
            except QueryCache.DoesNotExist:
                pass
        
        # Process with enhanced RAG
        start_time = time.time()
        
        try:
            # Get enhanced RAG system
            rag_system = get_enhanced_rag_system(use_local_embeddings=use_local_embeddings)
            
            # Perform search
            search_results = rag_system.search(query_text, doc_type=doc_type, top_k=5)
            
            # Generate answer
            answer_data = rag_system.generate_answer(query_text, search_results)
            
            processing_time = time.time() - start_time
            
            # Store in history
            query_history = QueryHistory.objects.create(
                query_text=query_text,
                answer=answer_data['answer'],
                sources=json.dumps(answer_data['sources']),
                confidence_score=answer_data['confidence_score'],
                processing_time=processing_time,
                doc_type=doc_type
            )
            
            # Cache if good confidence
            if answer_data['confidence_score'] >= 0.45 and use_cache:
                query_hash = hashlib.md5(f"{query_text}_{doc_type}".encode()).hexdigest()
                QueryCache.objects.create(
                    query_text=query_text,
                    query_hash=query_hash,
                    answer=answer_data['answer'],
                    sources=json.dumps(answer_data['sources']),
                    confidence_score=answer_data['confidence_score'],
                    doc_type=doc_type
                )
            
            # Return response
            return Response({
                'query': query_text,
                'answer': answer_data['answer'],
                'sources': answer_data['sources'],
                'search_results': search_results,
                'confidence_score': answer_data['confidence_score'],
                'from_cache': False,
                'processing_time': processing_time,
                'query_id': query_history.id,
                'search_metadata': answer_data.get('search_metadata', {})
            })
            
        except Exception as e:
            print(f"Enhanced RAG error: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to standard RAG
            try:
                from .search.real_rag import perform_rag_query
                
                rag_result = perform_rag_query(query_text, doc_type)
                processing_time = time.time() - start_time
                
                # Store in history
                query_history = QueryHistory.objects.create(
                    query_text=query_text,
                    answer=rag_result['answer'],
                    sources=json.dumps(rag_result['sources']),
                    confidence_score=rag_result['confidence_score'],
                    processing_time=processing_time,
                    doc_type=doc_type
                )
                
                return Response({
                    'query': query_text,
                    'answer': rag_result['answer'],
                    'sources': rag_result['sources'],
                    'search_results': rag_result.get('search_results', []),
                    'confidence_score': rag_result['confidence_score'],
                    'from_cache': False,
                    'processing_time': processing_time,
                    'query_id': query_history.id,
                    'search_metadata': {
                        'search_type': 'fallback_standard',
                        'error': str(e)
                    }
                })
            except Exception as fallback_error:
                return Response({
                    'error': 'Unable to process query',
                    'details': str(fallback_error)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([AllowAny])
class EnhancedSystemStatusView(APIView):
    """
    Check the status of the enhanced RAG system.
    """
    
    def get(self, request):
        """Get system status and statistics."""
        try:
            rag_system = get_enhanced_rag_system()
            
            # Get system stats
            doc_count = len(rag_system.search_engine.documents)
            index_size = rag_system.search_engine.index.ntotal if hasattr(rag_system.search_engine.index, 'ntotal') else 0
            
            # Test search
            test_results = rag_system.search("DNA repair", top_k=3)
            
            return Response({
                'status': 'operational',
                'statistics': {
                    'total_documents': doc_count,
                    'index_size': index_size,
                    'has_bm25': rag_system.search_engine.bm25 is not None,
                    'embedding_model': 'local' if rag_system.embedding_model else 'openai'
                },
                'test_search': {
                    'query': 'DNA repair',
                    'result_count': len(test_results),
                    'top_result': test_results[0]['title'] if test_results else None
                }
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)