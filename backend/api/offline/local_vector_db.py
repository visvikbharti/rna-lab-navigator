"""
Local vector database for offline/air-gapped operation.
Supports Qdrant, Chroma, and FAISS backends.
"""

import os
import logging
import json
import uuid
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import vector DB dependencies with graceful fallback
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("Qdrant not available. Install with: pip install qdrant-client")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available. Install with: pip install chromadb")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Install with: pip install faiss-cpu")


class LocalVectorDB:
    """
    Local vector database wrapper for offline operation.
    Provides API compatible with Weaviate client for easy swapping.
    """
    
    def __init__(self):
        """Initialize the local vector DB with config from settings"""
        self.config = getattr(settings, 'LOCAL_VECTOR_DB_CONFIG', {})
        self.engine_type = self.config.get('engine', 'qdrant').lower()
        self.db_path = self.config.get('path', '')
        self.client = None
        self.collections_initialized = set()
        
        # Create directory if it doesn't exist
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize the engine
        self._initialize_engine()
        
    def _initialize_engine(self):
        """Initialize the selected vector DB engine"""
        if self.engine_type == 'qdrant' and QDRANT_AVAILABLE:
            self._initialize_qdrant()
        elif self.engine_type == 'chroma' and CHROMA_AVAILABLE:
            self._initialize_chroma()
        elif self.engine_type == 'faiss' and FAISS_AVAILABLE:
            self._initialize_faiss()
        else:
            fallback = self._find_available_engine()
            if fallback:
                logger.warning(f"Selected engine {self.engine_type} not available. Using {fallback} instead.")
                self.engine_type = fallback
                self._initialize_engine()
            else:
                logger.error(f"No available vector DB engines. Please install qdrant-client, chromadb, or faiss-cpu.")
                
    def _find_available_engine(self) -> Optional[str]:
        """Find an available vector DB engine"""
        if QDRANT_AVAILABLE:
            return 'qdrant'
        elif CHROMA_AVAILABLE:
            return 'chroma'
        elif FAISS_AVAILABLE:
            return 'faiss'
        return None
    
    def _initialize_qdrant(self):
        """Initialize Qdrant client"""
        try:
            self.client = QdrantClient(path=self.db_path)
            logger.info(f"Initialized Qdrant client at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            
    def _initialize_chroma(self):
        """Initialize ChromaDB client"""
        try:
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"Initialized ChromaDB client at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            
    def _initialize_faiss(self):
        """Initialize FAISS client"""
        # FAISS needs custom wrapper implementation
        self.client = FAISSWrapper(self.db_path)
        logger.info(f"Initialized FAISS wrapper at {self.db_path}")
    
    def ensure_collection(self, collection_name: str, vector_size: int = 1536):
        """Ensure the collection exists, creating it if necessary"""
        if collection_name in self.collections_initialized:
            return
            
        try:
            if self.engine_type == 'qdrant':
                self._ensure_qdrant_collection(collection_name, vector_size)
            elif self.engine_type == 'chroma':
                self._ensure_chroma_collection(collection_name)
            elif self.engine_type == 'faiss':
                self._ensure_faiss_collection(collection_name, vector_size)
                
            self.collections_initialized.add(collection_name)
        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name}: {e}")
    
    def _ensure_qdrant_collection(self, collection_name: str, vector_size: int):
        """Ensure Qdrant collection exists"""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name not in collection_names:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=vector_size,
                    distance=qdrant_models.Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection {collection_name}")
    
    def _ensure_chroma_collection(self, collection_name: str):
        """Ensure ChromaDB collection exists"""
        try:
            self.client.get_collection(collection_name)
        except:
            self.client.create_collection(collection_name)
            logger.info(f"Created ChromaDB collection {collection_name}")
    
    def _ensure_faiss_collection(self, collection_name: str, vector_size: int):
        """Ensure FAISS collection exists"""
        self.client.ensure_collection(collection_name, vector_size)
        
    def add(self, collection_name: str, data_object: Dict[str, Any], 
            vector: List[float], document_id: str = None) -> str:
        """Add an item to the vector DB"""
        if self.client is None:
            logger.error("Vector DB client not initialized")
            return None
            
        # Ensure collection exists
        vector_size = len(vector)
        self.ensure_collection(collection_name, vector_size)
        
        # Generate UUID if not provided
        if document_id is None:
            document_id = str(uuid.uuid4())
            
        try:
            if self.engine_type == 'qdrant':
                return self._add_qdrant(collection_name, data_object, vector, document_id)
            elif self.engine_type == 'chroma':
                return self._add_chroma(collection_name, data_object, vector, document_id)
            elif self.engine_type == 'faiss':
                return self._add_faiss(collection_name, data_object, vector, document_id)
        except Exception as e:
            logger.error(f"Failed to add item to {collection_name}: {e}")
            return None
    
    def _add_qdrant(self, collection_name: str, data_object: Dict[str, Any], 
                   vector: List[float], document_id: str) -> str:
        """Add item to Qdrant"""
        self.client.upsert(
            collection_name=collection_name,
            points=[
                qdrant_models.PointStruct(
                    id=document_id,
                    vector=vector,
                    payload=data_object
                )
            ]
        )
        return document_id
    
    def _add_chroma(self, collection_name: str, data_object: Dict[str, Any], 
                   vector: List[float], document_id: str) -> str:
        """Add item to ChromaDB"""
        collection = self.client.get_collection(collection_name)
        
        # ChromaDB requires serializing the data object
        metadata = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                   for k, v in data_object.items()}
        
        collection.upsert(
            ids=[document_id],
            embeddings=[vector],
            metadatas=[metadata]
        )
        return document_id
    
    def _add_faiss(self, collection_name: str, data_object: Dict[str, Any], 
                  vector: List[float], document_id: str) -> str:
        """Add item to FAISS"""
        return self.client.add(collection_name, data_object, vector, document_id)
    
    def search(self, collection_name: str, query_vector: List[float] = None, 
               query_text: str = None, limit: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search the vector DB"""
        if self.client is None:
            logger.error("Vector DB client not initialized")
            return []
            
        if collection_name not in self.collections_initialized:
            logger.warning(f"Collection {collection_name} not initialized")
            return []
            
        try:
            if self.engine_type == 'qdrant':
                return self._search_qdrant(collection_name, query_vector, limit, filters)
            elif self.engine_type == 'chroma':
                return self._search_chroma(collection_name, query_vector, query_text, limit, filters)
            elif self.engine_type == 'faiss':
                return self._search_faiss(collection_name, query_vector, limit, filters)
            return []
        except Exception as e:
            logger.error(f"Failed to search {collection_name}: {e}")
            return []
    
    def _search_qdrant(self, collection_name: str, query_vector: List[float], 
                      limit: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search Qdrant"""
        # Convert filters to Qdrant format
        filter_conditions = None
        if filters:
            filter_conditions = self._convert_filters_to_qdrant(filters)
            
        # Perform search
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            filter=filter_conditions
        )
        
        # Format results
        results = []
        for hit in search_result:
            item = hit.payload.copy()
            item['_id'] = hit.id
            item['_score'] = hit.score
            results.append(item)
            
        return results
    
    def _convert_filters_to_qdrant(self, filters: Dict[str, Any]) -> qdrant_models.Filter:
        """Convert generic filters to Qdrant format"""
        conditions = []
        
        for key, value in filters.items():
            if key == 'doc_type' and value:
                conditions.append(
                    qdrant_models.FieldCondition(
                        key='doc_type',
                        match=qdrant_models.MatchValue(value=value)
                    )
                )
                
        if conditions:
            return qdrant_models.Filter(must=conditions)
        return None
    
    def _search_chroma(self, collection_name: str, query_vector: List[float], 
                      query_text: str, limit: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search ChromaDB"""
        collection = self.client.get_collection(collection_name)
        
        # Convert filters to ChromaDB format
        where_clause = None
        if filters:
            where_dict = {}
            if 'doc_type' in filters and filters['doc_type']:
                where_dict['doc_type'] = filters['doc_type']
            if where_dict:
                where_clause = where_dict
                
        # Perform search
        if query_vector:
            search_result = collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=where_clause
            )
        elif query_text:
            search_result = collection.query(
                query_texts=[query_text],
                n_results=limit,
                where=where_clause
            )
        else:
            return []
            
        # Format results
        results = []
        for i, (doc_id, metadata, distance) in enumerate(zip(
            search_result['ids'][0],
            search_result['metadatas'][0],
            search_result['distances'][0]
        )):
            # Parse JSON strings back to objects
            parsed_metadata = {}
            for k, v in metadata.items():
                try:
                    parsed_metadata[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    parsed_metadata[k] = v
                    
            item = parsed_metadata.copy()
            item['_id'] = doc_id
            item['_score'] = 1.0 - distance  # Convert distance to similarity score
            results.append(item)
            
        return results
    
    def _search_faiss(self, collection_name: str, query_vector: List[float], 
                     limit: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search FAISS"""
        return self.client.search(collection_name, query_vector, limit, filters)


class FAISSWrapper:
    """Custom wrapper for FAISS since it doesn't have a client like Qdrant or ChromaDB"""
    
    def __init__(self, db_path: str):
        """Initialize FAISS wrapper"""
        self.db_path = db_path
        self.indexes = {}  # FAISS indexes
        self.metadata = {}  # Metadata store
        self.id_maps = {}  # Maps internal FAISS ids to external ids
        
        # Load existing collections
        self._load_collections()
        
    def _load_collections(self):
        """Load existing FAISS collections from disk"""
        for filename in os.listdir(self.db_path):
            if filename.endswith('.index'):
                collection_name = filename[:-6]  # Remove .index suffix
                try:
                    # Load FAISS index
                    index_path = os.path.join(self.db_path, filename)
                    self.indexes[collection_name] = faiss.read_index(index_path)
                    
                    # Load metadata
                    metadata_path = os.path.join(self.db_path, f"{collection_name}.meta.json")
                    id_map_path = os.path.join(self.db_path, f"{collection_name}.ids.json")
                    
                    if os.path.exists(metadata_path) and os.path.exists(id_map_path):
                        with open(metadata_path, 'r') as f:
                            self.metadata[collection_name] = json.load(f)
                        with open(id_map_path, 'r') as f:
                            self.id_maps[collection_name] = json.load(f)
                            
                        logger.info(f"Loaded FAISS collection {collection_name}")
                except Exception as e:
                    logger.error(f"Failed to load FAISS collection {collection_name}: {e}")
    
    def ensure_collection(self, collection_name: str, vector_size: int):
        """Ensure FAISS collection exists"""
        if collection_name in self.indexes:
            return
            
        # Create new FAISS index
        index = faiss.IndexFlatIP(vector_size)  # Inner product (can be converted to cosine)
        self.indexes[collection_name] = index
        self.metadata[collection_name] = {}
        self.id_maps[collection_name] = {}
        
        logger.info(f"Created FAISS collection {collection_name}")
        
        # Save to disk
        self._save_collection(collection_name)
        
    def _save_collection(self, collection_name: str):
        """Save FAISS collection to disk"""
        if collection_name not in self.indexes:
            return
            
        try:
            # Save FAISS index
            index_path = os.path.join(self.db_path, f"{collection_name}.index")
            faiss.write_index(self.indexes[collection_name], index_path)
            
            # Save metadata
            metadata_path = os.path.join(self.db_path, f"{collection_name}.meta.json")
            id_map_path = os.path.join(self.db_path, f"{collection_name}.ids.json")
            
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata[collection_name], f)
            with open(id_map_path, 'w') as f:
                json.dump(self.id_maps[collection_name], f)
                
            logger.info(f"Saved FAISS collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to save FAISS collection {collection_name}: {e}")
    
    def add(self, collection_name: str, data_object: Dict[str, Any], 
           vector: List[float], document_id: str) -> str:
        """Add item to FAISS"""
        if collection_name not in self.indexes:
            logger.error(f"Collection {collection_name} not initialized")
            return None
            
        # Convert vector to numpy array
        vector_np = np.array([vector], dtype=np.float32)
        
        # Normalize vector for cosine similarity
        faiss.normalize_L2(vector_np)
        
        # Add to FAISS index
        index = self.indexes[collection_name]
        internal_id = index.ntotal  # Get the next available ID
        index.add(vector_np)
        
        # Store metadata and ID mapping
        self.metadata[collection_name][document_id] = data_object
        self.id_maps[collection_name][str(internal_id)] = document_id
        
        # Save updated collection
        self._save_collection(collection_name)
        
        return document_id
    
    def search(self, collection_name: str, query_vector: List[float], 
              limit: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search FAISS"""
        if collection_name not in self.indexes:
            logger.error(f"Collection {collection_name} not initialized")
            return []
            
        # Convert vector to numpy array
        query_vector_np = np.array([query_vector], dtype=np.float32)
        
        # Normalize vector for cosine similarity
        faiss.normalize_L2(query_vector_np)
        
        # Search FAISS index
        index = self.indexes[collection_name]
        distances, internal_ids = index.search(query_vector_np, limit)
        
        # Format results
        results = []
        for i, (distance, internal_id) in enumerate(zip(distances[0], internal_ids[0])):
            if internal_id == -1:  # FAISS returns -1 for empty slots
                continue
                
            doc_id = self.id_maps[collection_name].get(str(internal_id))
            if not doc_id:
                continue
                
            metadata = self.metadata[collection_name].get(doc_id, {})
            
            # Apply filters if provided
            if filters and not self._matches_filters(metadata, filters):
                continue
                
            item = metadata.copy()
            item['_id'] = doc_id
            item['_score'] = float(distance)  # Convert to float for JSON serialization
            results.append(item)
            
        return results
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches filters"""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True


def get_local_vector_db() -> LocalVectorDB:
    """Factory function to get a local vector DB instance"""
    return LocalVectorDB()