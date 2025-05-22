"""
Cross-encoder reranking for improved search relevance.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple

from sentence_transformers import CrossEncoder
from django.conf import settings

logger = logging.getLogger(__name__)

# Default model to use for cross-encoder reranking
DEFAULT_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Map of available cross-encoder models
CROSS_ENCODER_MODELS = {
    "default": DEFAULT_CROSS_ENCODER_MODEL,
    "ms-marco-small": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "ms-marco-large": "cross-encoder/ms-marco-MiniLM-L-12-v2",
    "ms-marco-multilingual": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
    "science": "nthakur/crossencoder-scifact"
}

# Singleton instance of the cross-encoder model
_cross_encoder_instance = None


def get_cross_encoder(model_name: str = None) -> CrossEncoder:
    """
    Get or create a cross-encoder model instance.
    Uses a singleton pattern to avoid loading the model multiple times.
    
    Args:
        model_name (str, optional): Name of the model to use. If not provided,
                                    uses the model specified in settings or the default.
    
    Returns:
        CrossEncoder: The cross-encoder model
    """
    global _cross_encoder_instance
    
    # If model is already instantiated, return it
    if _cross_encoder_instance is not None:
        return _cross_encoder_instance
    
    # Determine which model to use
    if model_name is None:
        # Check settings for default model
        model_name = getattr(settings, 'CROSS_ENCODER_MODEL', None)
        
        if model_name is None or model_name not in CROSS_ENCODER_MODELS:
            model_name = 'default'
    
    # Get the actual model path
    model_path = CROSS_ENCODER_MODELS.get(model_name, DEFAULT_CROSS_ENCODER_MODEL)
    
    try:
        logger.info(f"Loading cross-encoder model: {model_path}")
        start_time = time.time()
        
        # Load the model
        _cross_encoder_instance = CrossEncoder(model_path, max_length=512)
        
        logger.info(f"Cross-encoder model loaded in {time.time() - start_time:.2f}s")
        return _cross_encoder_instance
    except Exception as e:
        logger.error(f"Error loading cross-encoder model: {str(e)}")
        # Return None on error - the caller should handle this case
        return None


def rerank_search_results(query_text: str, results: List[Dict], 
                         top_k: Optional[int] = None, 
                         model_name: Optional[str] = None) -> Tuple[List[Dict], float]:
    """
    Rerank search results using a cross-encoder model.
    
    Args:
        query_text (str): The search query
        results (List[Dict]): Initial search results to rerank
        top_k (int, optional): Number of results to return after reranking
        model_name (str, optional): Name of the cross-encoder model to use
        
    Returns:
        Tuple[List[Dict], float]: Reranked results and time taken in ms
    """
    if not results:
        return results, 0
    
    start_time = time.time()
    
    # Get the cross-encoder model
    model = get_cross_encoder(model_name)
    if model is None:
        # If model loading failed, return original results
        logger.warning("Cross-encoder model not available, skipping reranking")
        return results, 0
    
    # Prepare query-document pairs for reranking
    query_doc_pairs = []
    for result in results:
        # Use content field for documents and caption for figures
        if "content" in result:
            text = result["content"]
        elif "caption" in result:
            text = result["caption"]
        else:
            # If neither field is present, use an empty string
            text = ""
        
        # Add to pairs for scoring
        query_doc_pairs.append([query_text, text])
    
    # Score all query-document pairs
    scores = model.predict(query_doc_pairs)
    
    # Add scores to results
    for i, score in enumerate(scores):
        results[i]["rerank_score"] = float(score)
    
    # Sort by rerank score
    reranked_results = sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)
    
    # Limit to top_k if specified
    if top_k is not None and top_k > 0:
        reranked_results = reranked_results[:top_k]
    
    elapsed_ms = (time.time() - start_time) * 1000
    return reranked_results, elapsed_ms


def rerank_chunks_for_rag(query_text: str, chunks: List[Dict], 
                         top_k: int = 5, 
                         model_name: Optional[str] = None) -> Tuple[List[Dict], float]:
    """
    Rerank document chunks for retrieval augmented generation.
    Specifically optimized for selecting the best context chunks for RAG.
    
    Args:
        query_text (str): The search query
        chunks (List[Dict]): Document chunks to rerank
        top_k (int): Number of chunks to return after reranking
        model_name (str, optional): Name of the cross-encoder model to use
        
    Returns:
        Tuple[List[Dict], float]: Reranked chunks and time taken in ms
    """
    if not chunks:
        return chunks, 0
    
    start_time = time.time()
    
    # Get the cross-encoder model
    model = get_cross_encoder(model_name)
    if model is None:
        # If model loading failed, return original chunks
        logger.warning("Cross-encoder model not available, skipping reranking for RAG")
        return chunks[:top_k], 0
    
    # Prepare query-chunk pairs for reranking
    query_chunk_pairs = []
    for chunk in chunks:
        # Use content field for chunk text
        chunk_text = chunk.get("content", "")
        
        # Add to pairs for scoring
        query_chunk_pairs.append([query_text, chunk_text])
    
    # Score all query-chunk pairs
    scores = model.predict(query_chunk_pairs)
    
    # Add scores to chunks
    for i, score in enumerate(scores):
        chunks[i]["rerank_score"] = float(score)
    
    # Sort by rerank score
    reranked_chunks = sorted(chunks, key=lambda x: x.get("rerank_score", 0), reverse=True)
    
    # Limit to top_k
    reranked_chunks = reranked_chunks[:top_k]
    
    elapsed_ms = (time.time() - start_time) * 1000
    return reranked_chunks, elapsed_ms