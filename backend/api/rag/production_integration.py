"""
Integration layer for Production RAG with existing chat interface.
"""

from typing import Dict, Any, List
import asyncio
from django.conf import settings

from .simple_production_rag import get_simple_production_rag
from .weaviate_production_rag import WeaviateProductionRAG
from .optimized_weaviate_rag import OptimizedWeaviateRAG
from api.search.real_rag import perform_rag_query


class ProductionRAGAdapter:
    """Adapter to integrate production RAG with existing interfaces."""
    
    def __init__(self):
        # Use stable Weaviate Production RAG with enhanced caching
        self.production_rag = WeaviateProductionRAG()
        self.use_production = getattr(settings, 'USE_PRODUCTION_RAG', True)
        
        # Performance optimization settings
        self.cache_ttl = getattr(settings, 'PRODUCTION_RAG_CACHE_TTL', 3600)
        self.enable_aggressive_caching = True
    
    async def process_query(self, query: str, session_id: str = None, 
                          user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process query with production RAG pipeline."""
        
        # If production RAG is disabled, fallback to basic RAG
        if not self.use_production:
            return await self._fallback_to_basic_rag(query)
        
        try:
            # Use production RAG
            result = self.production_rag.query(query)
            
            # Transform to expected format
            return {
                'answer': result['answer'],
                'sources': result['sources'],
                'confidence': result.get('confidence_score', result.get('confidence', 0.5)),  # Handle both keys
                'search_results': result.get('search_results', []),
                'metadata': result.get('metadata', {}),
                'reasoning_trace': [],  # Production RAG doesn't use reasoning trace
                'entities': self._extract_entities(result['answer']),
                'suggestions': self._generate_suggestions(query),
                'processing_time': result.get('processing_time', 0)
            }
            
        except Exception as e:
            print(f"[PRODUCTION RAG ERROR] {e}")
            # Fallback to basic RAG on error
            return await self._fallback_to_basic_rag(query)
    
    async def _fallback_to_basic_rag(self, query: str) -> Dict[str, Any]:
        """Fallback to basic RAG implementation."""
        try:
            # Run basic RAG in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, perform_rag_query, query)
            
            return {
                'answer': result.get('answer', 'No answer found'),
                'sources': result.get('sources', []),
                'confidence': result.get('confidence_score', 0.5),
                'search_results': result.get('search_results', []),
                'metadata': {},
                'reasoning_trace': [],
                'entities': [],
                'suggestions': self._generate_suggestions(query),
                'processing_time': result.get('processing_time', 0)
            }
        except Exception as e:
            print(f"[BASIC RAG ERROR] {e}")
            return {
                'answer': "I apologize, but I encountered an error processing your question. Please try again.",
                'sources': [],
                'confidence': 0,
                'search_results': [],
                'metadata': {'error': str(e)},
                'reasoning_trace': [],
                'entities': [],
                'suggestions': [],
                'processing_time': 0
            }
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities from text."""
        # Simple entity extraction - in production use NER
        entities = []
        
        # Extract capitalized words (potential entities)
        words = text.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                # Check if it's not start of sentence
                if i == 0 or words[i-1].endswith(('.', '!', '?')):
                    continue
                entities.append(word.strip('.,;:'))
        
        # Extract technical terms
        tech_terms = ['RNA', 'DNA', 'CRISPR', 'Cas9', 'FnCas9', 'PCR', 'TRIzol']
        for term in tech_terms:
            if term in text and term not in entities:
                entities.append(term)
        
        return list(set(entities))[:10]  # Limit to 10 entities
    
    def _generate_suggestions(self, query: str, answer: str = None) -> List[Dict[str, Any]]:
        """Generate intelligent follow-up suggestions based on query and answer context."""
        suggestions = []
        query_lower = query.lower()
        
        # Protocol-related suggestions
        if 'protocol' in query_lower or 'method' in query_lower:
            suggestions.extend([
                {'text': 'What are the common troubleshooting steps?', 'type': 'follow_up', 'confidence': 0.95},
                {'text': 'What materials and reagents do I need?', 'type': 'follow_up', 'confidence': 0.9},
                {'text': 'What are the critical steps to watch out for?', 'type': 'follow_up', 'confidence': 0.85},
                {'text': 'Show me alternative protocols for this', 'type': 'alternative', 'confidence': 0.8}
            ])
        
        # RNA/DNA related suggestions
        if any(term in query_lower for term in ['rna', 'dna', 'nucleic acid']):
            suggestions.extend([
                {'text': 'How do I check RNA/DNA quality and integrity?', 'type': 'quality', 'confidence': 0.9},
                {'text': 'What are the optimal storage conditions?', 'type': 'storage', 'confidence': 0.85},
                {'text': 'What concentration should I use?', 'type': 'technical', 'confidence': 0.8},
                {'text': 'How do I prevent degradation?', 'type': 'preservation', 'confidence': 0.85}
            ])
        
        # CRISPR-related suggestions
        if any(term in query_lower for term in ['crispr', 'cas9', 'gene editing']):
            suggestions.extend([
                {'text': 'What are the design considerations for guides?', 'type': 'design', 'confidence': 0.95},
                {'text': 'How do I validate the editing efficiency?', 'type': 'validation', 'confidence': 0.9},
                {'text': 'What are potential off-target effects?', 'type': 'safety', 'confidence': 0.85},
                {'text': 'Compare different CRISPR systems used in the lab', 'type': 'comparison', 'confidence': 0.8}
            ])
        
        # Disease/MLC related suggestions
        if any(term in query_lower for term in ['disease', 'mlc', 'patient', 'clinical']):
            suggestions.extend([
                {'text': 'What are the molecular mechanisms involved?', 'type': 'mechanism', 'confidence': 0.9},
                {'text': 'Are there any therapeutic approaches being tested?', 'type': 'therapy', 'confidence': 0.85},
                {'text': 'What cell models are available for this?', 'type': 'models', 'confidence': 0.8},
                {'text': 'Show me related clinical studies', 'type': 'clinical', 'confidence': 0.75}
            ])
        
        # Author/thesis related suggestions
        if any(name in query for name in ['Saumya', 'Kumar', 'Sundaram', 'Rhythm', 'Riya', 'Asgar', 'Meghali']):
            suggestions.extend([
                {'text': 'What other work has this author contributed to?', 'type': 'author', 'confidence': 0.95},
                {'text': 'Show me the key findings from this thesis', 'type': 'summary', 'confidence': 0.9},
                {'text': 'Compare with other theses on similar topics', 'type': 'comparison', 'confidence': 0.85},
                {'text': 'What techniques did they develop?', 'type': 'techniques', 'confidence': 0.8}
            ])
        
        # Experiment/research suggestions
        if any(term in query_lower for term in ['experiment', 'research', 'study', 'investigate']):
            suggestions.extend([
                {'text': 'What controls should I include?', 'type': 'controls', 'confidence': 0.95},
                {'text': 'How many replicates are recommended?', 'type': 'statistics', 'confidence': 0.9},
                {'text': 'What are the expected outcomes?', 'type': 'prediction', 'confidence': 0.85},
                {'text': 'Show me similar experiments in the lab', 'type': 'similar', 'confidence': 0.8}
            ])
        
        # General contextual suggestions
        suggestions.extend([
            {'text': 'Can you explain this in simpler terms?', 'type': 'simplify', 'confidence': 0.7},
            {'text': 'What are the next steps I should consider?', 'type': 'next_steps', 'confidence': 0.75},
            {'text': 'Are there any recent updates on this topic?', 'type': 'updates', 'confidence': 0.65},
            {'text': 'Show me related publications from the lab', 'type': 'related', 'confidence': 0.7}
        ])
        
        # Sort by confidence and deduplicate
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Return top 5 unique suggestions
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s['text'] not in seen and len(unique_suggestions) < 5:
                seen.add(s['text'])
                unique_suggestions.append(s)
        
        return unique_suggestions


# Singleton instance
_adapter_instance = None

def get_production_rag_adapter():
    """Get singleton adapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = ProductionRAGAdapter()
    return _adapter_instance