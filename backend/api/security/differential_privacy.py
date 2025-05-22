"""
Differential privacy utilities for RNA Lab Navigator.
This module provides DP mechanisms to protect embeddings and query results.
"""

import numpy as np
import logging
import hashlib
from typing import List, Dict, Any, Optional, Union, Tuple
from functools import lru_cache
from django.conf import settings

logger = logging.getLogger(__name__)


class DPEmbeddingProtector:
    """
    Adds differential privacy protections to embeddings.
    Uses calibrated noise to protect against embedding inversion attacks.
    """
    
    def __init__(
        self,
        epsilon: float = 0.1,
        sensitivity: float = 0.1,
        clip_norm: float = 1.0,
        noise_mechanism: str = "gaussian"
    ):
        """
        Initialize the DP embedding protector.
        
        Args:
            epsilon: Privacy parameter (lower = more privacy)
            sensitivity: L2 sensitivity of embeddings
            clip_norm: Maximum L2 norm for clipping
            noise_mechanism: 'gaussian' or 'laplace'
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.clip_norm = clip_norm
        self.noise_mechanism = noise_mechanism.lower()
        
        # Set noise scale based on mechanism
        if self.noise_mechanism == "gaussian":
            # For Gaussian, scale is based on sensitivity/epsilon
            self.noise_scale = self.sensitivity / self.epsilon
        elif self.noise_mechanism == "laplace":
            # For Laplace, scale is sensitivity/epsilon
            self.noise_scale = self.sensitivity / self.epsilon
        else:
            raise ValueError(f"Unsupported noise mechanism: {noise_mechanism}")
            
        logger.info(f"Initialized DP Embedding Protector: "
                   f"epsilon={self.epsilon}, "
                   f"mechanism={self.noise_mechanism}, "
                   f"noise_scale={self.noise_scale}")
    
    def _clip_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Clip embedding to maximum L2 norm.
        
        Args:
            embedding: Embedding vector
            
        Returns:
            Clipped embedding vector
        """
        # Convert to numpy array if not already
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)
            
        # Calculate L2 norm
        norm = np.linalg.norm(embedding)
        
        # Clip if norm exceeds threshold
        if norm > self.clip_norm:
            return embedding * (self.clip_norm / norm)
        else:
            return embedding
    
    def _add_noise(self, embedding: np.ndarray) -> np.ndarray:
        """
        Add calibrated noise to embedding.
        
        Args:
            embedding: Embedding vector
            
        Returns:
            Noisy embedding vector
        """
        # Get embedding shape
        shape = embedding.shape
        
        # Generate noise based on mechanism
        if self.noise_mechanism == "gaussian":
            noise = np.random.normal(0, self.noise_scale, shape)
        elif self.noise_mechanism == "laplace":
            noise = np.random.laplace(0, self.noise_scale, shape)
        else:
            raise ValueError(f"Unsupported noise mechanism: {self.noise_mechanism}")
            
        # Add noise to embedding
        noisy_embedding = embedding + noise
        
        # Renormalize to unit length
        norm = np.linalg.norm(noisy_embedding)
        if norm > 0:
            noisy_embedding = noisy_embedding / norm
            
        return noisy_embedding
    
    def protect_embedding(self, embedding: Union[List[float], np.ndarray]) -> np.ndarray:
        """
        Apply differential privacy protection to embedding.
        
        Args:
            embedding: Embedding vector (list or numpy array)
            
        Returns:
            Protected embedding vector
        """
        # Convert to numpy array if needed
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)
            
        # Skip if embedding protection is disabled
        if not getattr(settings, 'ENABLE_DP_EMBEDDING_PROTECTION', False):
            return embedding
            
        # Apply protection
        clipped = self._clip_embedding(embedding)
        protected = self._add_noise(clipped)
        
        return protected
    
    @staticmethod
    def embedding_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine distance between two embeddings.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
            
        Returns:
            Cosine distance (1 - similarity)
        """
        # Convert to numpy arrays if needed
        if not isinstance(emb1, np.ndarray):
            emb1 = np.array(emb1)
        if not isinstance(emb2, np.ndarray):
            emb2 = np.array(emb2)
            
        # Normalize
        emb1_norm = np.linalg.norm(emb1)
        emb2_norm = np.linalg.norm(emb2)
        
        if emb1_norm == 0 or emb2_norm == 0:
            return 1.0  # Maximum distance
            
        emb1 = emb1 / emb1_norm
        emb2 = emb2 / emb2_norm
        
        # Calculate cosine similarity
        similarity = np.dot(emb1, emb2)
        
        # Return distance (1 - similarity)
        return 1.0 - similarity


# Hash-based deterministic noise
@lru_cache(maxsize=1024)
def get_deterministic_noise(embedding_hash: str, dim: int, scale: float) -> np.ndarray:
    """
    Generate deterministic noise vector from hash.
    Uses document hash to ensure consistent noise application.
    
    Args:
        embedding_hash: Hash of document content
        dim: Embedding dimension
        scale: Noise scale factor
    
    Returns:
        Deterministic noise vector
    """
    # Use hash as seed
    seed = int(embedding_hash[:8], 16)
    np.random.seed(seed)
    
    # Generate noise
    noise = np.random.normal(0, scale, dim)
    
    # Reset random seed
    np.random.seed(None)
    
    return noise


def protect_embedding_deterministic(
    embedding: Union[List[float], np.ndarray],
    document_id: str,
    content_hash: Optional[str] = None,
    scale: float = 0.05
) -> np.ndarray:
    """
    Apply deterministic differential privacy to embedding.
    Uses document hash to ensure consistent noise application.
    
    Args:
        embedding: Embedding vector
        document_id: Document identifier
        content_hash: Optional hash of content
        scale: Noise scale factor
        
    Returns:
        Protected embedding
    """
    # Convert to numpy array if needed
    if not isinstance(embedding, np.ndarray):
        embedding = np.array(embedding)
        
    # Skip if embedding protection is disabled
    if not getattr(settings, 'ENABLE_DP_EMBEDDING_PROTECTION', False):
        return embedding
        
    # Generate content hash if not provided
    if content_hash is None:
        content_hash = hashlib.sha256(str(document_id).encode()).hexdigest()
        
    # Get embedding dimension
    dim = embedding.shape[0]
    
    # Get deterministic noise
    noise = get_deterministic_noise(content_hash, dim, scale)
    
    # Add noise
    protected = embedding + noise
    
    # Normalize
    norm = np.linalg.norm(protected)
    if norm > 0:
        protected = protected / norm
        
    return protected


# Default protector instance
_default_protector = None

def get_embedding_protector() -> DPEmbeddingProtector:
    """Get default embedding protector instance"""
    global _default_protector
    if _default_protector is None:
        epsilon = getattr(settings, 'DP_EPSILON', 0.1)
        sensitivity = getattr(settings, 'DP_SENSITIVITY', 0.1)
        clip_norm = getattr(settings, 'DP_CLIP_NORM', 1.0)
        noise_mechanism = getattr(settings, 'DP_NOISE_MECHANISM', 'gaussian')
        
        _default_protector = DPEmbeddingProtector(
            epsilon=epsilon,
            sensitivity=sensitivity,
            clip_norm=clip_norm,
            noise_mechanism=noise_mechanism
        )
    return _default_protector


def protect_embedding(embedding: Union[List[float], np.ndarray]) -> np.ndarray:
    """
    Apply differential privacy protection to embedding.
    Convenience wrapper for the default protector.
    
    Args:
        embedding: Embedding vector
        
    Returns:
        Protected embedding
    """
    return get_embedding_protector().protect_embedding(embedding)