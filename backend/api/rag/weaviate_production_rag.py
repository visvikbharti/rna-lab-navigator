"""
Weaviate-based Production RAG - Queries Weaviate directly
"""

import time
import hashlib
import json
import weaviate
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
from openai import OpenAI


class WeaviateProductionRAG:
    """Production RAG that queries Weaviate directly."""
    
    def __init__(self):
        # Initialize OpenAI
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.cache_ttl = getattr(settings, 'PRODUCTION_RAG_CACHE_TTL', 3600)
        self.max_context_chars = 10000  # Reduced for faster processing
        self.top_k = 4  # Reduced from 5 for faster retrieval
        
        # Connect to Weaviate
        self.weaviate_client = weaviate.Client("http://localhost:8080")
        
        # Disabled preloading to improve performance - was causing 70+ second delays
        # self._preload_common_queries()
    
    def query(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """Enhanced RAG query using Weaviate directly."""
        start_time = time.time()
        
        # Check cache
        if use_cache:
            cache_key = f"weaviate_rag:{hashlib.md5(question.encode()).hexdigest()}"
            cached = cache.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Search using Weaviate's hybrid search (BM25 + vector)
        try:
            # Use BM25 for keyword matching
            result = self.weaviate_client.query.get(
                "Document",
                ["content", "title", "author", "doc_type", "year", "chapter"]
            ).with_bm25(
                query=question,
                properties=["content", "title", "author"]
            ).with_limit(self.top_k * 3).do()
            
            if 'errors' in result:
                print(f"Weaviate error: {result['errors']}")
                return self._error_response(start_time)
            
            documents = result.get('data', {}).get('Get', {}).get('Document', [])
            
            if not documents:
                return {
                    'answer': "I couldn't find any relevant information in the lab documents for your question.",
                    'sources': [],
                    'confidence_score': 0.0,
                    'search_results': [],
                    'processing_time': time.time() - start_time,
                    'metadata': {'status': 'no_results'}
                }
            
            # Convert to format expected by other methods
            search_results = []
            for doc in documents:
                search_results.append({
                    'text': doc['content'],
                    'metadata': {
                        'title': doc.get('title', 'Unknown'),
                        'author': doc.get('author', 'Unknown'),
                        'doc_type': doc.get('doc_type', 'unknown'),
                        'year': doc.get('year', ''),
                        'chapter': doc.get('chapter', '')
                    },
                    'score': 1.0  # Weaviate doesn't return scores for BM25
                })
            
            # Build context from results
            context = self._build_context(search_results[:self.top_k])
            
            # Generate answer
            answer = self._generate_answer(question, context, search_results[:self.top_k])
            
            # Extract unique sources
            sources = self._extract_sources(search_results[:self.top_k])
            
            # Calculate confidence
            confidence = self._calculate_confidence(search_results[:self.top_k], answer)
            
            response = {
                'answer': answer,
                'sources': sources,
                'confidence_score': confidence,
                'search_results': [
                    {
                        'title': r['metadata'].get('title', 'Unknown'),
                        'author': r['metadata'].get('author', 'Unknown'), 
                        'score': r.get('score', 0),
                        'snippet': r.get('text', '')[:300] + "...",
                        'type': r['metadata'].get('doc_type', 'unknown')
                    }
                    for r in search_results[:self.top_k]
                ],
                'processing_time': time.time() - start_time,
                'metadata': {
                    'total_results': len(documents),
                    'context_length': len(context)
                }
            }
            
            # Cache result
            if use_cache and confidence > 0.4:
                cache.set(cache_key, json.dumps(response), timeout=self.cache_ttl)
            
            return response
            
        except Exception as e:
            print(f"Weaviate query error: {e}")
            return self._error_response(start_time)
    
    def _build_context(self, results: List[Dict]) -> str:
        """Build context from search results."""
        context_parts = []
        total_chars = 0
        
        for i, result in enumerate(results):
            if total_chars >= self.max_context_chars:
                break
                
            text = result['text']
            metadata = result['metadata']
            
            # Add source header
            source_header = f"[Source {i+1}: {metadata['title']} by {metadata['author']}, {metadata['year']}]"
            
            # Calculate remaining space
            remaining_chars = self.max_context_chars - total_chars - len(source_header) - 10
            
            if remaining_chars > 100:
                if len(text) > remaining_chars:
                    text = text[:remaining_chars] + "..."
                
                context_parts.append(f"{source_header}\\n{text}")
                total_chars += len(source_header) + len(text) + 10
        
        return "\\n\\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str, sources: List[Dict]) -> str:
        """Generate answer using OpenAI."""
        prompt = f"""You are an expert research assistant for Dr. Debojyoti Chakraborty's RNA biology lab at CSIR-IGIB. 

Context from lab documents:
{context}

Question: {question}

Instructions:
1. Provide a comprehensive answer based on the provided context
2. Include specific details like protocols, concentrations, timings when available
3. Cite sources naturally in the flow (e.g., "According to [Author's] thesis...")
4. If the context doesn't contain relevant information, provide general scientific knowledge but clearly state it's not from lab documents

Remember: Be helpful, specific, and practical for lab members."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Use gpt-4o for fast responses
                messages=[
                    {"role": "system", "content": "You are an expert RNA biology research assistant. Be concise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,  # Reduced for faster response
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            import traceback
            print(f"OpenAI error: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"API Key set: {'Yes' if self.openai_client.api_key else 'No'}")
            print(f"API Key length: {len(self.openai_client.api_key) if self.openai_client.api_key else 0}")
            return "I apologize, but I encountered an error while generating the answer."
    
    def _extract_sources(self, results: List[Dict]) -> List[Dict]:
        """Extract unique sources from results."""
        unique_sources = {}
        
        for result in results:
            metadata = result['metadata']
            key = f"{metadata['title']}_{metadata['author']}_{metadata['year']}"
            
            if key not in unique_sources:
                unique_sources[key] = {
                    'title': metadata['title'],
                    'author': metadata['author'],
                    'year': metadata['year'],
                    'type': metadata.get('doc_type', 'unknown')
                }
        
        return list(unique_sources.values())[:3]  # Limit to 3 sources
    
    def _calculate_confidence(self, results: List[Dict], answer: str) -> float:
        """Calculate confidence score."""
        if not results:
            return 0.0
        
        # Base confidence on number of results
        base_confidence = min(0.5 + (len(results) * 0.1), 0.9)
        
        # Adjust based on answer quality
        if "I don't have" in answer or "not mentioned" in answer:
            base_confidence *= 0.7
        
        return round(base_confidence, 2)
    
    def _error_response(self, start_time: float) -> Dict[str, Any]:
        """Return error response."""
        return {
            'answer': "I apologize, but I encountered an error while searching the documents.",
            'sources': [],
            'confidence_score': 0.0,
            'search_results': [],
            'processing_time': time.time() - start_time,
            'metadata': {'status': 'error'}
        }
    def _preload_common_queries(self):
        """Preload cache with common queries for instant responses."""
        common_queries = [
            "What is RNA extraction protocol?",
            "Tell me about CRISPR-Cas9",
            "What is MLC disease?",
            "How to do Western blot?",
            "What are the lab protocols?",
            "Explain gene editing techniques"
        ]
        
        print("[WEAVIATE RAG] Preloading common queries...")
        for query in common_queries:
            try:
                # Query without using cache to generate fresh results
                self.query(query, use_cache=False)
                print(f"  ✓ Preloaded: {query}")
            except Exception as e:
                print(f"  ✗ Failed to preload {query}: {e}")
