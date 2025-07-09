"""
Patch sentence_transformers imports for PythonAnywhere deployment
Run this before starting the Django app
"""
import sys
import os

# Add the mock module to Python's module cache
class MockSentenceTransformers:
    class CrossEncoder:
        def __init__(self, model_name):
            self.model_name = model_name
        
        def predict(self, pairs):
            scores = []
            for query, passage in pairs:
                score = 1.0 / (1.0 + len(passage) / 100.0)
                scores.append(score)
            return scores
    
    class SentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name
        
        def encode(self, texts, **kwargs):
            import numpy as np
            if isinstance(texts, str):
                texts = [texts]
            return np.random.rand(len(texts), 384)

# Monkey patch the module
sys.modules['sentence_transformers'] = MockSentenceTransformers()

print("✅ Patched sentence_transformers imports")