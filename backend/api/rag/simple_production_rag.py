"""
Simplified Production RAG - Direct integration with existing vector store.
"""

import time
import hashlib
import json
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
import openai

from api.search.real_rag import vector_store, perform_rag_query


class SimpleProductionRAG:
    """Production RAG that enhances the existing system."""
    
    def __init__(self):
        # Initialize OpenAI
        openai.api_key = settings.OPENAI_API_KEY
        self.cache_ttl = getattr(settings, 'PRODUCTION_RAG_CACHE_TTL', 3600)
        self.max_context_chars = 12000  # ~3000 tokens
        self.top_k = getattr(settings, 'PRODUCTION_RAG_FINAL_TOP_K', 5)
    
    def query(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """Enhanced RAG query with better context and ranking."""
        start_time = time.time()
        
        # Check cache
        if use_cache:
            cache_key = f"prod_rag:{hashlib.md5(question.encode()).hexdigest()}"
            cached = cache.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Use existing vector store search with higher k for better recall
        search_results = vector_store.search(question, top_k=self.top_k * 3)
        
        if not search_results:
            return {
                'answer': "I couldn't find any relevant information in the lab documents for your question.",
                'sources': [],
                'confidence': 0.0,
                'search_results': [],
                'processing_time': time.time() - start_time,
                'metadata': {'status': 'no_results'}
            }
        
        # Rerank results based on relevance
        reranked = self._rerank_results(question, search_results)
        
        # Build optimized context
        context = self._build_context(reranked)
        
        # Generate answer with better prompting
        answer = self._generate_answer(question, context)
        
        # Extract sources
        sources = self._extract_sources(reranked)
        
        # Calculate confidence
        confidence = self._calculate_confidence(reranked, answer)
        
        response = {
            'answer': answer,
            'sources': sources,
            'confidence': confidence,
            'search_results': [
                {
                    'title': r['metadata'].get('title', 'Unknown'),
                    'author': r['metadata'].get('author', 'Unknown'), 
                    'score': r.get('score', 0),
                    'snippet': r.get('text', '')[:200] + "..."
                }
                for r in reranked[:3]
            ],
            'processing_time': time.time() - start_time,
            'metadata': {
                'total_results': len(search_results),
                'reranked_results': len(reranked),
                'context_length': len(context)
            }
        }
        
        # Cache result
        if use_cache:
            cache.set(cache_key, json.dumps(response), timeout=self.cache_ttl)
        
        return response
    
    def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Rerank results for better relevance."""
        # Extract key terms from query
        query_terms = set(query.lower().split())
        
        # Score each result
        for result in results:
            text = result.get('text', '').lower()
            metadata = result.get('metadata', {})
            
            # Base score from vector similarity
            score = result.get('score', 0.0)
            
            # Boost for exact query matches
            if query.lower() in text:
                score += 0.5
            
            # Boost for title/author matches
            title = metadata.get('title', '').lower()
            author = metadata.get('author', '').lower()
            all_authors = metadata.get('all_authors', '').lower()
            
            for term in query_terms:
                if term in title:
                    score += 0.3
                if term in author or term in all_authors:
                    score += 0.2
            
            # Boost for document type relevance
            doc_type = metadata.get('doc_type', '').lower()
            if 'protocol' in query.lower() and doc_type == 'protocol':
                score += 0.4
            elif 'paper' in query.lower() and doc_type == 'paper':
                score += 0.4
            elif 'thesis' in query.lower() and doc_type == 'thesis':
                score += 0.4
            
            result['reranked_score'] = score
        
        # Sort by reranked score
        results.sort(key=lambda x: x.get('reranked_score', 0), reverse=True)
        
        # Return top results with good scores
        min_score = getattr(settings, 'PRODUCTION_RAG_MIN_RELEVANCE', 0.7)
        return [r for r in results if r.get('reranked_score', 0) >= min_score][:self.top_k]
    
    def _build_context(self, results: List[Dict]) -> str:
        """Build optimized context from results."""
        if not results:
            return ""
        
        # Group by document
        doc_groups = {}
        for result in results:
            metadata = result.get('metadata', {})
            key = (metadata.get('title', 'Unknown'), metadata.get('author', 'Unknown'))
            if key not in doc_groups:
                doc_groups[key] = []
            doc_groups[key].append(result)
        
        # Build context with document headers
        context_parts = []
        current_length = 0
        
        for (title, author), chunks in doc_groups.items():
            # Add document header
            doc_type = chunks[0].get('metadata', {}).get('doc_type', 'Document')
            # Get all authors if available
            all_authors = chunks[0].get('metadata', {}).get('all_authors', author)
            header = f"\n### {doc_type}: {title} by {all_authors}\n"
            context_parts.append(header)
            current_length += len(header)
            
            # Add chunks
            for chunk in chunks:
                text = chunk.get('text', '')
                if current_length + len(text) > self.max_context_chars:
                    # Add partial chunk if there's room
                    remaining = self.max_context_chars - current_length
                    if remaining > 100:  # Only add if meaningful
                        context_parts.append(text[:remaining] + "...")
                    break
                
                context_parts.append(text + "\n")
                current_length += len(text) + 1
            
            if current_length >= self.max_context_chars * 0.9:
                break
        
        return "".join(context_parts).strip()
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer with improved prompting."""
        if not context:
            return "I couldn't find relevant information to answer your question."
        
        prompt = f"""You are an expert research assistant helping scientists in Dr. Chakraborty's RNA biology lab.

Available context from lab documents:
{context}

Question: {question}

Instructions:
1. Answer ONLY based on the provided context - do not use external knowledge
2. If the context doesn't fully answer the question, acknowledge what's missing
3. Be specific with technical details (concentrations, temperatures, times, volumes)
4. Naturally mention which document the information comes from
5. If multiple documents have relevant info, synthesize them coherently

Answer:"""

        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a knowledgeable research assistant for an RNA biology lab. Provide accurate, detailed answers based solely on the provided documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return "I apologize, but I encountered an error generating the response. Please try again."
    
    def _extract_sources(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Extract unique sources from results."""
        seen = set()
        sources = []
        
        for result in results:
            metadata = result.get('metadata', {})
            key = (metadata.get('title'), metadata.get('author'))
            
            if key not in seen and key[0]:  # Ensure title exists
                seen.add(key)
                sources.append({
                    'title': metadata.get('title', 'Unknown'),
                    'author': metadata.get('author', 'Unknown'),
                    'year': metadata.get('year', 2024),
                    'type': metadata.get('doc_type', 'document')
                })
        
        return sources
    
    def _calculate_confidence(self, results: List[Dict], answer: str) -> float:
        """Calculate answer confidence based on results and answer quality."""
        if not results:
            return 0.0
        
        # Base confidence from result scores
        avg_score = sum(r.get('reranked_score', 0) for r in results) / len(results)
        
        # Boost confidence if answer cites sources
        if any(phrase in answer.lower() for phrase in ['according to', 'states that', 'mentions', 'describes']):
            avg_score += 0.1
        
        # Reduce confidence for uncertain phrases
        if any(phrase in answer.lower() for phrase in ["i couldn't find", "not available", "doesn't contain"]):
            avg_score *= 0.5
        
        return min(avg_score, 1.0)


# Singleton instance
_simple_rag_instance = None

def get_simple_production_rag() -> SimpleProductionRAG:
    """Get singleton instance."""
    global _simple_rag_instance
    if _simple_rag_instance is None:
        _simple_rag_instance = SimpleProductionRAG()
    return _simple_rag_instance