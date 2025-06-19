"""
Simplified hybrid search implementation without advanced dependencies.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
import openai
from django.conf import settings
import pickle
import os
from collections import defaultdict
import re


class SimpleHybridSearchEngine:
    """
    Simplified hybrid search combining semantic search with TF-IDF keyword search.
    """
    
    def __init__(self, embedding_dim: int = 1536):
        self.embedding_dim = embedding_dim
        
        # Simple numpy arrays for semantic search
        self.embeddings = []
        self.documents = []
        self.metadata = []
        
        # TF-IDF for keyword search
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        
        # Caching
        self.cache_dir = "/tmp/hybrid_search_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load existing data if available
        self.load_from_cache()
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to both semantic and keyword indices.
        
        Args:
            documents: List of dicts with 'text', 'embedding', and 'metadata'
        """
        for doc in documents:
            # Add to document store
            self.documents.append(doc['text'])
            self.metadata.append(doc['metadata'])
            
            # Add embedding
            embedding = np.array(doc['embedding'], dtype=np.float32)
            embedding = normalize([embedding])[0]  # L2 normalize
            self.embeddings.append(embedding)
        
        # Rebuild TF-IDF index
        if self.documents:
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents)
        
        # Save to cache
        self.save_to_cache()
    
    def search(self, query: str, top_k: int = 10, 
               semantic_weight: float = 0.7,
               keyword_weight: float = 0.3) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        
        Returns:
            List of search results with combined scores
        """
        if not self.documents:
            return []
        
        # Get more candidates for re-ranking
        candidate_k = min(top_k * 3, len(self.documents))
        
        # Semantic search
        semantic_results = self._semantic_search(query, candidate_k)
        
        # Keyword search
        keyword_results = self._keyword_search(query, candidate_k)
        
        # Combine results
        combined_results = self._combine_results(
            semantic_results, 
            keyword_results,
            semantic_weight,
            keyword_weight
        )
        
        # Re-rank with additional features
        reranked_results = self._rerank_results(combined_results, query)
        
        return reranked_results[:top_k]
    
    def _semantic_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Perform semantic search using embeddings."""
        if not self.embeddings:
            return []
        
        # Get query embedding
        query_embedding = self._get_embedding(query)
        query_embedding = normalize([query_embedding])[0]
        
        # Calculate cosine similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = np.dot(query_embedding, doc_embedding)
            similarities.append((i, float(similarity)))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def _keyword_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Perform keyword search using TF-IDF."""
        if self.tfidf_matrix is None:
            return []
        
        # Transform query
        query_vector = self.tfidf_vectorizer.transform([query])
        
        # Calculate similarities
        similarities = (self.tfidf_matrix * query_vector.T).toarray().flatten()
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append((idx, float(similarities[idx])))
        
        return results
    
    def _combine_results(self, semantic_results: List[Tuple[int, float]], 
                        keyword_results: List[Tuple[int, float]],
                        semantic_weight: float,
                        keyword_weight: float) -> List[Dict[str, Any]]:
        """Combine semantic and keyword search results."""
        combined_scores = defaultdict(lambda: {'semantic': 0.0, 'keyword': 0.0})
        
        # Add semantic scores
        for doc_id, score in semantic_results:
            combined_scores[doc_id]['semantic'] = score
        
        # Add keyword scores
        for doc_id, score in keyword_results:
            # Normalize TF-IDF scores to 0-1 range
            normalized_score = min(score * 2, 1.0)  # Simple normalization
            combined_scores[doc_id]['keyword'] = normalized_score
        
        # Calculate combined scores
        results = []
        for doc_id, scores in combined_scores.items():
            combined_score = (
                semantic_weight * scores['semantic'] +
                keyword_weight * scores['keyword']
            )
            
            results.append({
                'doc_id': doc_id,
                'text': self.documents[doc_id],
                'metadata': self.metadata[doc_id],
                'score': combined_score,
                'semantic_score': scores['semantic'],
                'keyword_score': scores['keyword']
            })
        
        # Sort by combined score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def _rerank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Re-rank results with additional features.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for result in results:
            boost = 0.0
            text_lower = result['text'].lower()
            
            # Exact phrase match
            if query_lower in text_lower:
                boost += 0.3
            
            # Author name boost
            if 'author' in result['metadata']:
                author = result['metadata']['author'].lower()
                for word in query_words:
                    if word in author:
                        boost += 0.5
            
            # Title match boost
            if 'title' in result['metadata']:
                title = result['metadata']['title'].lower()
                matching_words = sum(1 for word in query_words if word in title)
                boost += 0.2 * (matching_words / len(query_words))
            
            # Document type boost
            if 'doc_type' in result['metadata']:
                doc_type = result['metadata']['doc_type']
                if 'thesis' in query_lower and doc_type == 'thesis':
                    boost += 0.3
                elif 'protocol' in query_lower and doc_type == 'protocol':
                    boost += 0.3
                elif 'paper' in query_lower and doc_type == 'paper':
                    boost += 0.2
            
            # Apply boost
            result['original_score'] = result['score']
            result['score'] = min(1.0, result['score'] + boost)
            result['boost'] = boost
        
        # Re-sort by boosted score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using OpenAI."""
        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000]
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return np.random.rand(self.embedding_dim)
    
    def save_to_cache(self):
        """Save indices to cache."""
        try:
            with open(os.path.join(self.cache_dir, "search_data.pkl"), 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadata': self.metadata,
                    'embeddings': self.embeddings,
                    'tfidf_vectorizer': self.tfidf_vectorizer,
                    'tfidf_matrix': self.tfidf_matrix
                }, f)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def load_from_cache(self):
        """Load indices from cache."""
        try:
            data_path = os.path.join(self.cache_dir, "search_data.pkl")
            if os.path.exists(data_path):
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.metadata = data.get('metadata', [])
                    self.embeddings = data.get('embeddings', [])
                    self.tfidf_vectorizer = data.get('tfidf_vectorizer', self.tfidf_vectorizer)
                    self.tfidf_matrix = data.get('tfidf_matrix', None)
                
                print(f"Loaded {len(self.documents)} documents from cache")
        except Exception as e:
            print(f"Error loading cache: {e}")


class LocalEmbeddingModel:
    """
    Simple fallback embedding model using TF-IDF when sentence-transformers isn't available.
    """
    
    def __init__(self, model_name: str = "tfidf"):
        self.model_name = model_name
        self.vectorizer = TfidfVectorizer(max_features=1536)
        self.is_fitted = False
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text."""
        try:
            # Try OpenAI first
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000]
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            print(f"Error getting OpenAI embedding: {e}")
            # Fallback to random embedding
            return np.random.rand(1536)