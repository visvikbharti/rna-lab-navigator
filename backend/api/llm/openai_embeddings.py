"""
OpenAI embeddings integration for non-isolated environments.
Provides vector embeddings using OpenAI's API.
"""

import logging
from django.conf import settings
from openai import OpenAI

# Set up logging
logger = logging.getLogger(__name__)

class OpenAIEmbeddingModel:
    """
    OpenAI embedding model wrapper.
    Provides vector embeddings using OpenAI's API.
    """
    
    def __init__(self, api_key=None, model=None):
        """
        Initialize OpenAI embedding model.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to settings.OPENAI_API_KEY.
            model (str, optional): Embedding model name. Defaults to settings.OPENAI_EMBEDDING_MODEL.
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI embedding model: {self.model}")
    
    def create(self, input=None, model=None, encoding_format=None):
        """
        Create embeddings for the given input.
        
        Args:
            input (str or list): Text to embed
            model (str, optional): Model name. Defaults to self.model.
            encoding_format (str, optional): Output format. Defaults to None.
        
        Returns:
            dict: Embeddings response from OpenAI
        """
        try:
            model = model or self.model
            
            response = self.client.embeddings.create(
                input=input,
                model=model,
                encoding_format=encoding_format
            )
            
            return response
        except Exception as e:
            logger.error(f"Error creating OpenAI embeddings: {str(e)}")
            raise


# Global instance for convenience
_embedding_model = None

def get_embedding_model():
    """Get or create global embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = OpenAIEmbeddingModel()
    return _embedding_model


def get_embeddings(texts, model=None):
    """
    Get embeddings for a list of texts.
    
    Args:
        texts (list): List of texts to embed
        model (str, optional): Model name
        
    Returns:
        list: List of embedding vectors
    """
    try:
        embedding_model = get_embedding_model()
        
        # Ensure texts is a list
        if isinstance(texts, str):
            texts = [texts]
        
        response = embedding_model.create(input=texts, model=model)
        
        # Extract embedding vectors
        embeddings = []
        for data in response.data:
            embeddings.append(data.embedding)
        
        return embeddings
        
    except Exception as e:
        logger.error(f"Error getting embeddings: {str(e)}")
        # Return zero vectors as fallback
        import numpy as np
        return [np.zeros(1536).tolist() for _ in texts]  # Ada-002 dimension