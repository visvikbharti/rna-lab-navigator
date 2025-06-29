"""
Hybrid search implementation combining semantic search with BM25 keyword search.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
import faiss
from sklearn.preprocessing import normalize
from openai import OpenAI
from django.conf import settings
import pickle
import os
from collections import defaultdict
import re


class HybridSearchEngine:
    """
    Combines semantic search (embeddings) with keyword search (BM25) for better retrieval.
    """
    
    def __init__(self, embedding_dim: int = 1536):
        self.embedding_dim = embedding_dim
        
        # FAISS index for semantic search
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity
        self.index = faiss.IndexIDMap(self.index)  # Add ID mapping
        
        # BM25 for keyword search
        self.bm25 = None
        self.documents = []
        self.metadata = []
        self.doc_tokens = []
        
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
            doc_id = len(self.documents)
            
            # Add to document store
            self.documents.append(doc['text'])
            self.metadata.append(doc['metadata'])
            
            # Tokenize for BM25
            tokens = self._tokenize(doc['text'])
            self.doc_tokens.append(tokens)
            
            # Add embedding to FAISS
            embedding = np.array(doc['embedding'], dtype=np.float32)
            embedding = normalize([embedding])[0]  # L2 normalize for cosine similarity
            self.index.add_with_ids(
                np.array([embedding]),
                np.array([doc_id], dtype=np.int64)
            )
        
        # Rebuild BM25 index
        self._rebuild_bm25()
        
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
        # Get more candidates for re-ranking
        candidate_k = top_k * 3
        
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
        # Get query embedding
        query_embedding = self._get_embedding(query)
        query_embedding = normalize([query_embedding])[0]
        
        # Search in FAISS
        scores, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            min(top_k, self.index.ntotal)
        )
        
        # Convert to list of (doc_id, score) tuples
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx != -1:  # Valid result
                results.append((int(idx), float(score)))
        
        return results
    
    def _keyword_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Perform keyword search using BM25."""
        if not self.bm25:
            return []
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top k results
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Normalize scores to 0-1 range
        max_score = max(scores) if max(scores) > 0 else 1
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                normalized_score = scores[idx] / max_score
                results.append((idx, normalized_score))
        
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
            combined_scores[doc_id]['keyword'] = score
        
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
        Re-rank results with additional features like exact matches, 
        technical term matches, and recency.
        """
        query_lower = query.lower()
        query_terms = set(self._tokenize(query))
        
        for result in results:
            boost = 0.0
            text_lower = result['text'].lower()
            
            # Exact phrase match
            if query_lower in text_lower:
                boost += 0.3
            
            # Technical term matches
            tech_terms = self._extract_technical_terms(query)
            for term in tech_terms:
                if term.lower() in text_lower:
                    boost += 0.1
            
            # Author name boost
            if 'author' in result['metadata']:
                author = result['metadata']['author'].lower()
                for term in query_terms:
                    if term in author:
                        boost += 0.5
            
            # Title match boost
            if 'title' in result['metadata']:
                title = result['metadata']['title'].lower()
                matching_terms = sum(1 for term in query_terms if term in title)
                boost += 0.2 * (matching_terms / len(query_terms))
            
            # Recency boost (if year is available)
            if 'year' in result['metadata']:
                try:
                    year = int(result['metadata']['year'])
                    if year >= 2020:
                        boost += 0.1
                except:
                    pass
            
            # Document type boost
            if 'doc_type' in result['metadata']:
                doc_type = result['metadata']['doc_type']
                # Boost based on query intent
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
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep scientific notation
        text = re.sub(r'[^\w\s\.\-\+]', ' ', text)
        
        # Split into tokens
        tokens = text.split()
        
        # Remove stopwords (basic list - can be expanded)
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'about', 'as', 'is', 'was', 'are', 'were',
            'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'them'
        }
        
        tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
        
        return tokens
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms from text."""
        technical_patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms (RNA, DNA, CRISPR)
            r'\b\w+\d+\w*\b',  # Terms with numbers (Cas9, COVID-19)
            r'\b\w+-\w+\b',    # Hyphenated terms
        ]
        
        terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, text)
            terms.extend(matches)
        
        # Add known technical terms
        known_terms = {
            'crispr', 'cas9', 'rna', 'dna', 'pcr', 'qpcr', 'western',
            'blot', 'sequencing', 'genome', 'gene', 'protein', 'enzyme',
            'nhej', 'hdr', 'homology', 'repair', 'cleavage', 'mutation'
        }
        
        for term in text.lower().split():
            if term in known_terms:
                terms.append(term)
        
        return list(set(terms))
    
    def _rebuild_bm25(self):
        """Rebuild BM25 index."""
        if self.doc_tokens:
            self.bm25 = BM25Okapi(self.doc_tokens)
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using OpenAI."""
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(
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
            # Save FAISS index
            faiss.write_index(self.index, os.path.join(self.cache_dir, "faiss.index"))
            
            # Save other data
            with open(os.path.join(self.cache_dir, "search_data.pkl"), 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadata': self.metadata,
                    'doc_tokens': self.doc_tokens
                }, f)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def load_from_cache(self):
        """Load indices from cache."""
        try:
            # Load FAISS index
            index_path = os.path.join(self.cache_dir, "faiss.index")
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
            
            # Load other data
            data_path = os.path.join(self.cache_dir, "search_data.pkl")
            if os.path.exists(data_path):
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.metadata = data.get('metadata', [])
                    self.doc_tokens = data.get('doc_tokens', [])
                
                # Rebuild BM25
                self._rebuild_bm25()
                
                print(f"Loaded {len(self.documents)} documents from cache")
        except Exception as e:
            print(f"Error loading cache: {e}")


class LocalEmbeddingModel:
    """
    Local embedding model using sentence-transformers for cost reduction.
    Falls back to OpenAI if needed.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.use_local = True
        
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            print(f"Loaded local embedding model: {model_name}")
        except Exception as e:
            print(f"Failed to load local model, falling back to OpenAI: {e}")
            self.use_local = False
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text."""
        if self.use_local and self.model:
            # Use local model
            embedding = self.model.encode(text, convert_to_numpy=True)
            # Pad or truncate to match OpenAI's dimension if needed
            if len(embedding) < 1536:
                embedding = np.pad(embedding, (0, 1536 - len(embedding)), 'constant')
            elif len(embedding) > 1536:
                embedding = embedding[:1536]
            return embedding
        else:
            # Fall back to OpenAI
            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text[:8000]
                )
                return np.array(response.data[0].embedding)
            except Exception as e:
                print(f"Error getting embedding: {e}")
                return np.random.rand(1536)