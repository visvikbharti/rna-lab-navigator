"""
Enhanced RAG (Retrieval Augmented Generation) utilities.
Improves the RAG pipeline with cross-encoder reranking and other optimizations.
"""

import logging
import time
from typing import List, Dict, Any, Optional

from ..search.reranking import rerank_chunks_for_rag

logger = logging.getLogger(__name__)

def enhance_rag_context(query: str, chunks: List[Dict], max_context_chunks: int = 5) -> List[Dict]:
    """
    Enhance the RAG context by applying cross-encoder reranking and other optimizations.
    
    Args:
        query (str): The user query
        chunks (List[Dict]): The initial chunks retrieved from the vector search
        max_context_chunks (int): Maximum number of chunks to include in the context
    
    Returns:
        List[Dict]: The optimized chunks for RAG
    """
    if not chunks:
        logger.warning("No chunks provided for RAG enhancement")
        return chunks
    
    # Apply cross-encoder reranking to improve chunk selection
    reranked_chunks, reranking_time_ms = rerank_chunks_for_rag(
        query_text=query,
        chunks=chunks,
        top_k=max_context_chunks
    )
    
    logger.info(f"Reranked {len(chunks)} chunks to {len(reranked_chunks)} in {reranking_time_ms:.2f}ms")
    
    # Apply additional enhancements for RAG context
    enhanced_chunks = _optimize_chunks_for_rag(reranked_chunks)
    
    return enhanced_chunks


def _optimize_chunks_for_rag(chunks: List[Dict]) -> List[Dict]:
    """
    Apply additional optimizations to chunks for RAG.
    
    Args:
        chunks (List[Dict]): The reranked chunks
    
    Returns:
        List[Dict]: The optimized chunks
    """
    # For now, we'll just add source information in a format that's easier
    # for the LLM to use in citations
    for i, chunk in enumerate(chunks):
        # Create a concise citation string
        citation_parts = []
        
        if chunk.get('title'):
            citation_parts.append(f"\"{chunk['title']}\"")
        
        if chunk.get('doc_type'):
            citation_parts.append(chunk['doc_type'])
        
        if chunk.get('author'):
            citation_parts.append(f"by {chunk['author']}")
        
        if chunk.get('year'):
            citation_parts.append(f"({chunk['year']})")
        
        if chunk.get('chapter'):
            citation_parts.append(f"Chapter {chunk['chapter']}")
        
        # Add a citation field that's easy for the LLM to use
        chunk['citation'] = ", ".join(citation_parts)
        
        # Add a citation token that the LLM can use
        chunk['citation_token'] = f"[{i+1}]"
    
    return chunks