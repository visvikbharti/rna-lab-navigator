"""
Mock sentence_transformers module for PythonAnywhere deployment
This prevents import errors when sentence_transformers is not available
"""

class CrossEncoder:
    """Mock CrossEncoder that returns a simple score"""
    def __init__(self, model_name):
        self.model_name = model_name
    
    def predict(self, pairs):
        """Return mock scores"""
        # Return a simple score based on text length similarity
        scores = []
        for query, passage in pairs:
            # Simple heuristic: shorter passages get higher scores
            score = 1.0 / (1.0 + len(passage) / 100.0)
            scores.append(score)
        return scores

class SentenceTransformer:
    """Mock SentenceTransformer"""
    def __init__(self, model_name):
        self.model_name = model_name
    
    def encode(self, texts, **kwargs):
        """Return mock embeddings"""
        import numpy as np
        if isinstance(texts, str):
            texts = [texts]
        # Return random embeddings of dimension 384
        return np.random.rand(len(texts), 384)