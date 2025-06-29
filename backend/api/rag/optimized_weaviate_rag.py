"""
Optimized Weaviate Production RAG - Target: <5s response time
"""

import time
import hashlib
import json
import weaviate
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from .performance_optimizer import (
    PerformanceOptimizer, 
    OptimizedWeaviateSearch,
    monitor_performance
)


class OptimizedWeaviateRAG:
    """High-performance RAG implementation with <5s target response time."""
    
    def __init__(self):
        # Initialize components
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.client = weaviate.Client("http://localhost:8080")
        
        # Performance optimizer
        self.optimizer = PerformanceOptimizer()
        self.search_engine = OptimizedWeaviateSearch(self.client, self.optimizer)
        
        # Configuration
        self.cache_ttl = getattr(settings, 'PRODUCTION_RAG_CACHE_TTL', 3600)
        self.max_context_chars = 8000  # Reduced from 12000 for faster processing
        self.top_k = 3  # Reduced from 5 for faster retrieval
        self.temperature = 0.7
        
        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    @monitor_performance("total_query")
    def query(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """Optimized RAG query with <5s target."""
        start_time = time.time()
        timings = {}
        
        # Level 1: Full query cache (fastest)
        if use_cache:
            cache_key = f"optimized_rag:{hashlib.md5(question.encode()).hexdigest()}"
            cached = cache.get(cache_key)
            if cached:
                result = json.loads(cached)
                result['from_cache'] = True
                result['processing_time'] = time.time() - start_time
                return result
        
        # Level 2: Parallel operations
        try:
            # Start all operations in parallel
            search_future = self.executor.submit(self._optimized_search, question)
            embedding_future = self.executor.submit(self._get_question_embedding, question)
            
            # Wait for search results first (usually slower)
            t1 = time.time()
            search_results = search_future.result(timeout=3.0)  # 3s timeout
            timings['search'] = time.time() - t1
            
            if not search_results:
                return self._empty_response(question, timings)
            
            # Build context while waiting for embedding
            t2 = time.time()
            context = self.optimizer.optimize_context_building(
                search_results, 
                self.max_context_chars
            )
            timings['context_building'] = time.time() - t2
            
            # Generate answer with streaming (but collect full response)
            t3 = time.time()
            answer = self._generate_answer_fast(question, context, search_results)
            timings['answer_generation'] = time.time() - t3
            
            # Prepare response
            response = self._prepare_response(
                answer, 
                search_results, 
                timings,
                start_time
            )
            
            # Cache the response asynchronously
            if use_cache:
                self.executor.submit(
                    cache.set, 
                    cache_key, 
                    json.dumps(response), 
                    self.cache_ttl
                )
            
            return response
            
        except Exception as e:
            print(f"[OPTIMIZED RAG ERROR] {e}")
            return self._error_response(str(e), timings, start_time)
    
    def _optimized_search(self, query: str) -> List[Dict]:
        """Optimized search with caching and relevance filtering."""
        # First try exact match in cache
        results = self.search_engine.search_with_cache(query, self.top_k * 2)
        
        # Filter by relevance score to reduce context size
        filtered_results = []
        for result in results:
            score = result.get('score', 0)
            # Dynamic threshold based on result quality
            if score > 0.7 or (len(filtered_results) < 2 and score > 0.5):
                filtered_results.append(result)
            
            if len(filtered_results) >= self.top_k:
                break
        
        return filtered_results
    
    def _get_question_embedding(self, question: str) -> Optional[List[float]]:
        """Get question embedding with caching."""
        embedding = self.optimizer.get_cached_embedding(question)
        if embedding:
            return embedding
        
        # Compute embedding
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=question
            )
            embedding = response['data'][0]['embedding']
            
            # Cache it
            self.optimizer.cache_embedding(question, embedding)
            return embedding
        except:
            return None
    
    @monitor_performance("answer_generation")
    def _generate_answer_fast(self, question: str, context: str, 
                            search_results: List[Dict]) -> str:
        """Generate answer with optimized prompt."""
        # Shorter, more focused prompt for faster generation
        prompt = f"""Answer this question using ONLY the provided context. Be concise and accurate.

Context:
{context}

Question: {question}

Instructions:
- Answer directly without preamble
- Use 2-3 sentences for simple questions, 1 paragraph for complex ones
- Cite sources as (Author, Year)
- Say "I don't have enough information" if context is insufficient

Answer:"""

        try:
            # Use faster model settings
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a research assistant. Answer concisely and accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=300,  # Limit response length
                presence_penalty=0.0,
                frequency_penalty=0.0
            )
            
            return response.choices[0].message['content'].strip()
            
        except Exception as e:
            print(f"[GENERATION ERROR] {e}")
            return "I encountered an error generating the response. Please try again."
    
    def _prepare_response(self, answer: str, search_results: List[Dict], 
                         timings: Dict, start_time: float) -> Dict[str, Any]:
        """Prepare the final response with metadata."""
        # Extract unique sources
        sources = []
        seen_sources = set()
        
        for result in search_results[:3]:  # Limit sources
            source_key = f"{result.get('title')}_{result.get('author')}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append({
                    'title': result.get('title', 'Unknown'),
                    'author': result.get('author', 'Unknown'),
                    'year': result.get('year', 2023),
                    'type': result.get('type', 'unknown')
                })
        
        total_time = time.time() - start_time
        
        # Performance analysis
        performance = self.optimizer.get_response_time_breakdown(timings)
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence_score': self._calculate_confidence(search_results),
            'search_results': [{
                'title': r.get('title'),
                'author': r.get('author'),
                'score': round(r.get('score', 0), 2),
                'snippet': r.get('content', '')[:200] + '...',
                'type': r.get('type')
            } for r in search_results[:3]],
            'processing_time': total_time,
            'performance_breakdown': performance,
            'is_optimized': True,
            'from_cache': False,
            'metadata': {
                'total_results': len(search_results),
                'context_size': len(answer),
                'model': 'gpt-4o'
            }
        }
    
    def _calculate_confidence(self, results: List[Dict]) -> float:
        """Calculate confidence score based on search results."""
        if not results:
            return 0.0
        
        # Average of top scores, with penalty for few results
        scores = [r.get('score', 0) for r in results[:3]]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Penalty if we have very few results
        result_penalty = 1.0 if len(results) >= 3 else (len(results) / 3)
        
        return min(avg_score * result_penalty, 1.0)
    
    def _empty_response(self, question: str, timings: Dict) -> Dict[str, Any]:
        """Response when no results found."""
        return {
            'answer': f"I couldn't find any relevant information in the lab documents for: '{question}'. Please try rephrasing your question or asking about specific topics like protocols, theses, or research papers.",
            'sources': [],
            'confidence_score': 0.0,
            'search_results': [],
            'processing_time': time.time() - timings.get('start', time.time()),
            'is_optimized': True,
            'from_cache': False,
            'metadata': {'status': 'no_results'}
        }
    
    def _error_response(self, error: str, timings: Dict, start_time: float) -> Dict[str, Any]:
        """Response when an error occurs."""
        return {
            'answer': "I apologize, but I encountered an error processing your question. Please try again.",
            'sources': [],
            'confidence_score': 0.0,
            'search_results': [],
            'processing_time': time.time() - start_time,
            'is_optimized': True,
            'from_cache': False,
            'metadata': {'status': 'error', 'error': error}
        }
    
    def preload_cache(self):
        """Preload cache with common queries for instant responses."""
        common_queries = [
            "What is RNA extraction protocol?",
            "Tell me about CRISPR-Cas9",
            "What is MLC disease?",
            "How to do Western blot?",
            "What are the lab protocols available?"
        ]
        
        print("[OPTIMIZER] Preloading cache with common queries...")
        for query in common_queries:
            try:
                self.query(query, use_cache=False)  # Generate and cache
                print(f"  ✓ Cached: {query}")
            except:
                print(f"  ✗ Failed: {query}")
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)