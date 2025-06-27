"""
Performance optimization for RAG queries to achieve <5s response time.
"""
import time
import hashlib
import json
import pickle
from typing import List, Dict, Any, Optional, AsyncGenerator
from django.conf import settings
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import functools


class PerformanceOptimizer:
    """Optimizations to reduce response time from 12s to <5s."""
    
    def __init__(self):
        self.embedding_cache_ttl = 86400  # 24 hours for embeddings
        self.query_cache_ttl = 3600  # 1 hour for full queries
        self.search_cache_ttl = 1800  # 30 minutes for search results
        
        # Pre-compute common query embeddings on startup
        self.precomputed_embeddings = {}
        self._precompute_common_embeddings()
    
    def _precompute_common_embeddings(self):
        """Pre-compute embeddings for common queries."""
        common_queries = [
            "RNA extraction protocol",
            "CRISPR-Cas9 system",
            "Western blot protocol",
            "PCR protocol",
            "MLC disease",
            "gene editing",
            "DNA extraction",
            "cell culture protocol",
            "protein purification",
            "thesis findings"
        ]
        
        print("[OPTIMIZER] Pre-computing embeddings for common queries...")
        for query in common_queries:
            embedding = self.get_cached_embedding(query)
            if embedding:
                self.precomputed_embeddings[query.lower()] = embedding
    
    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache or compute and cache it."""
        # Check if it's a common query
        text_lower = text.lower()
        for common_query, embedding in self.precomputed_embeddings.items():
            if common_query in text_lower:
                return embedding
        
        # Check Redis cache
        cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        cached = cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Compute embedding (this is where we'd call OpenAI)
        # For now, return None to indicate it needs computation
        return None
    
    def cache_embedding(self, text: str, embedding: List[float]):
        """Cache an embedding."""
        cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        cache.set(cache_key, json.dumps(embedding), self.embedding_cache_ttl)
    
    def get_cached_search_results(self, query: str, top_k: int) -> Optional[List[Dict]]:
        """Get cached search results."""
        cache_key = f"search:{hashlib.md5(f'{query}:{top_k}'.encode()).hexdigest()}"
        cached = cache.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    def cache_search_results(self, query: str, top_k: int, results: List[Dict]):
        """Cache search results."""
        cache_key = f"search:{hashlib.md5(f'{query}:{top_k}'.encode()).hexdigest()}"
        cache.set(cache_key, json.dumps(results), self.search_cache_ttl)
    
    def batch_process_embeddings(self, texts: List[str]) -> Dict[str, List[float]]:
        """Process multiple embeddings in batch for efficiency."""
        results = {}
        texts_to_compute = []
        
        # Check cache first
        for text in texts:
            embedding = self.get_cached_embedding(text)
            if embedding:
                results[text] = embedding
            else:
                texts_to_compute.append(text)
        
        # Batch compute remaining embeddings
        if texts_to_compute:
            # In production, this would batch call OpenAI
            # For now, we'll simulate with placeholder
            for text in texts_to_compute:
                results[text] = None  # Placeholder
        
        return results
    
    async def parallel_search(self, queries: List[str], search_func) -> List[Dict]:
        """Execute multiple searches in parallel."""
        loop = asyncio.get_event_loop()
        
        async def search_wrapper(query):
            return await loop.run_in_executor(None, search_func, query)
        
        tasks = [search_wrapper(query) for query in queries]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def optimize_context_building(self, documents: List[Dict], max_chars: int) -> str:
        """Optimize context building with early stopping."""
        context_parts = []
        current_chars = 0
        
        # Sort by relevance score first
        sorted_docs = sorted(documents, key=lambda x: x.get('score', 0), reverse=True)
        
        for doc in sorted_docs:
            content = doc.get('content', '')
            
            # Early stopping if we have enough context
            if current_chars + len(content) > max_chars:
                remaining_chars = max_chars - current_chars
                if remaining_chars > 100:  # Only add if meaningful
                    context_parts.append(content[:remaining_chars] + "...")
                break
            
            context_parts.append(content)
            current_chars += len(content)
        
        return '\n\n'.join(context_parts)
    
    def get_response_time_breakdown(self, timings: Dict[str, float]) -> Dict[str, Any]:
        """Analyze response time breakdown."""
        total_time = sum(timings.values())
        breakdown = {
            'total_time': total_time,
            'components': {}
        }
        
        for component, time_taken in timings.items():
            breakdown['components'][component] = {
                'time': time_taken,
                'percentage': (time_taken / total_time * 100) if total_time > 0 else 0
            }
        
        # Identify bottlenecks
        bottlenecks = []
        for component, data in breakdown['components'].items():
            if data['percentage'] > 30:  # More than 30% of total time
                bottlenecks.append(component)
        
        breakdown['bottlenecks'] = bottlenecks
        
        return breakdown


class OptimizedWeaviateSearch:
    """Optimized Weaviate search with caching and batching."""
    
    def __init__(self, client, optimizer: PerformanceOptimizer):
        self.client = client
        self.optimizer = optimizer
        self.batch_size = 20  # Optimal batch size for Weaviate
    
    def search_with_cache(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search with caching layer."""
        # Check cache first
        cached_results = self.optimizer.get_cached_search_results(query, top_k)
        if cached_results:
            return cached_results
        
        # Perform search
        start_time = time.time()
        
        # Use hybrid search for better results
        result = self.client.query.get(
            "Document",
            ["content", "title", "author", "doc_type", "year"]
        ).with_hybrid(
            query=query,
            alpha=0.75  # 75% vector, 25% keyword
        ).with_limit(top_k).do()
        
        search_time = time.time() - start_time
        
        # Process results
        documents = []
        if 'data' in result and 'Get' in result['data'] and 'Document' in result['data']['Get']:
            for doc in result['data']['Get']['Document']:
                documents.append({
                    'content': doc.get('content', ''),
                    'title': doc.get('title', 'Unknown'),
                    'author': doc.get('author', 'Unknown'),
                    'score': doc.get('_additional', {}).get('score', 0),
                    'type': doc.get('doc_type', 'unknown')
                })
        
        # Cache results
        self.optimizer.cache_search_results(query, top_k, documents)
        
        return documents
    
    def batch_search(self, queries: List[str], top_k: int = 5) -> List[List[Dict]]:
        """Perform batch search for multiple queries."""
        results = []
        
        # Process in batches
        for i in range(0, len(queries), self.batch_size):
            batch = queries[i:i + self.batch_size]
            batch_results = []
            
            # Check cache for each query in batch
            for query in batch:
                result = self.search_with_cache(query, top_k)
                batch_results.append(result)
            
            results.extend(batch_results)
        
        return results


class StreamingResponseGenerator:
    """Generate responses in streaming fashion for better perceived performance."""
    
    def __init__(self):
        self.chunk_size = 50  # Characters per chunk
        self.initial_delay = 0.1  # Initial delay before streaming
        self.chunk_delay = 0.05  # Delay between chunks
    
    async def stream_response(self, text: str) -> AsyncGenerator[str, None]:
        """Stream response text in chunks."""
        # Initial delay for processing feel
        await asyncio.sleep(self.initial_delay)
        
        # Stream in chunks
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i:i + self.chunk_size]
            yield chunk
            
            # Small delay between chunks for natural feel
            if i + self.chunk_size < len(text):
                await asyncio.sleep(self.chunk_delay)


# Performance monitoring decorator
def monitor_performance(component_name: str):
    """Decorator to monitor performance of functions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            
            # Log slow operations
            if elapsed_time > 2.0:  # More than 2 seconds
                print(f"[PERF WARNING] {component_name} took {elapsed_time:.2f}s")
            
            # Add timing to result if it's a dict
            if isinstance(result, dict) and 'timings' not in result:
                result['timings'] = {}
            if isinstance(result, dict):
                result['timings'][component_name] = elapsed_time
            
            return result
        
        return wrapper
    return decorator