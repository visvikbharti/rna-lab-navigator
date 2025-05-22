"""
LLM integration package for RNA Lab Navigator.
Provides access to local and remote language models with network isolation.
"""

import os
import logging
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

def get_llm_client(isolation_level="auto"):
    """
    Get the appropriate LLM client based on settings and isolation requirements.
    
    Args:
        isolation_level (str): Desired isolation level:
            - "auto": Use settings.LLM_NETWORK_ISOLATION
            - "isolated": Force network isolation (use on-prem if available)
            - "public": Force public API usage (if allowed)
    
    Returns:
        Client object for interacting with LLM
    """
    # Determine if we should use isolated mode
    use_isolated = isolation_level == "isolated"
    
    # If auto, check settings
    if isolation_level == "auto":
        use_isolated = getattr(settings, 'LLM_NETWORK_ISOLATION', False)
    
    # If we're using isolation but it's not available, log a warning
    if use_isolated and not hasattr(settings, 'OLLAMA_API_URL'):
        logger.warning("LLM network isolation requested but no on-prem LLM configured. Falling back to OpenAI API.")
        use_isolated = False
    
    # If we're using public API but it's not allowed, raise an error
    if not use_isolated and getattr(settings, 'LLM_FORCE_ISOLATION', False):
        raise ValueError("Public LLM API usage is not allowed in this environment due to security policy.")
    
    # Get the appropriate client
    if use_isolated:
        from .local_llm import get_ollama_client
        return get_ollama_client()
    else:
        from openai import OpenAI
        return OpenAI(api_key=settings.OPENAI_API_KEY)


def is_llm_isolated():
    """Check if LLM is running in network-isolated mode."""
    return getattr(settings, 'LLM_NETWORK_ISOLATION', False)


def get_embedding_model():
    """
    Get the appropriate embedding model based on settings.
    In isolated mode, uses a local embedding model.
    """
    if is_llm_isolated():
        from .local_embeddings import LocalEmbeddingModel
        return LocalEmbeddingModel()
    else:
        # Use OpenAI's embedding model in non-isolated mode
        from .openai_embeddings import OpenAIEmbeddingModel
        return OpenAIEmbeddingModel()