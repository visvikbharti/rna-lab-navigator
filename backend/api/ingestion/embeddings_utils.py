"""
Utility functions for generating embeddings and interacting with the vector store.
"""

import hashlib
from django.conf import settings
from ..offline import get_llm_client, get_vector_db_client, is_offline_mode
from ..security.differential_privacy import protect_embedding, protect_embedding_deterministic


def create_embeddings(text):
    """
    Generate embeddings for a single text.
    
    Args:
        text (str): Text to create embeddings for
        
    Returns:
        list: Vector embedding for the text
    """
    # Use the existing generate_embedding function
    return generate_embedding(text)


def create_document_embeddings(document_data, chunks):
    """
    Create embeddings for document chunks.
    
    Args:
        document_data (dict): Document metadata
        chunks (list): List of text chunks to embed
        
    Returns:
        list: List of documents with embeddings
    """
    if not chunks:
        return []
    
    embedded_chunks = []
    
    for chunk in chunks:
        # Create embedding for this chunk
        embedding = create_embeddings(chunk)
        
        # Create document object with embedding
        doc_with_embedding = {
            **document_data,  # Include all metadata
            "content": chunk,  # Text content of this chunk
            "embedding": embedding  # Add the embedding
        }
        
        embedded_chunks.append(doc_with_embedding)
    
    return embedded_chunks


def get_weaviate_client():
    """
    Get a configured vector database client.
    Works with both Weaviate in online mode and local vector DB in offline mode.
    
    Returns:
        Client: Vector database client (Weaviate or local equivalent)
    """
    return get_vector_db_client()


def create_schema_if_not_exists():
    """
    Create the Weaviate schema if it doesn't exist.
    
    Returns:
        bool: True if schema was created, False if it already existed
    """
    client = get_weaviate_client()
    
    # Check if classes already exist
    schema = client.schema.get()
    existing_classes = [c['class'] for c in schema.get('classes', [])]
    schema_created = False
    
    if 'Document' not in existing_classes:
        # Define the Document class schema
        class_obj = {
            "class": "Document",
            "description": "A chunk of text from a document with metadata",
            "vectorizer": "text2vec-openai",  # Use OpenAI's embeddings
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada-002",
                    "modelVersion": "002",
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "content",
                    "description": "The text content of the chunk",
                    "dataType": ["text"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "doc_type",
                    "description": "Type of document (thesis, protocol, paper, etc.)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "title",
                    "description": "Title of the source document",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "author",
                    "description": "Author of the document",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "year",
                    "description": "Year of publication",
                    "dataType": ["int"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "chapter",
                    "description": "Chapter number (for theses)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "source",
                    "description": "Source identifier (filename, url, etc.)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                }
            ]
        }
        
        # Create the Document class
        client.schema.create_class(class_obj)
        schema_created = True

    # Create Figure class if it doesn't exist
    if 'Figure' not in existing_classes:
        figure_class = {
            "class": "Figure",
            "description": "An extracted figure or table from a document with caption",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada-002",
                    "modelVersion": "002",
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "figure_id",
                    "description": "Unique identifier for the figure",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "figure_type",
                    "description": "Type of figure (image, table, chart, etc.)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "caption",
                    "description": "Caption or description of the figure",
                    "dataType": ["text"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "page_number",
                    "description": "Page number where the figure appears",
                    "dataType": ["int"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "file_path",
                    "description": "Path to the stored figure file",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "doc_type",
                    "description": "Type of document (thesis, protocol, paper, etc.)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "title",
                    "description": "Title of the source document",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "author",
                    "description": "Author of the document",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "year",
                    "description": "Year of publication",
                    "dataType": ["int"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                }
            ]
        }
        
        # Create the Figure class
        client.schema.create_class(figure_class)
        schema_created = True
    
    return schema_created


def get_openai_client():
    """
    Get a configured LLM client.
    Works with both OpenAI in online mode and local LLM in offline mode.
    
    Returns:
        Client: LLM client (OpenAI or local equivalent)
    """
    return get_llm_client()


def generate_embedding(text):
    """
    Generate an embedding for the given text.
    Works with both OpenAI in online mode and local embeddings in offline mode.
    
    Args:
        text (str): Text to embed
        
    Returns:
        list: Vector embedding
    """
    if not text:
        return []
    
    # Truncate text if it's too long
    max_tokens = 8000  # Safe limit for text-embedding-ada-002
    # Rough approximation: 1 token ≈ 4 chars in English
    if len(text) > max_tokens * 4:
        text = text[:max_tokens * 4]
    
    client = get_openai_client()
    
    try:
        if is_offline_mode():
            # For local models, use the embeddings interface
            response = client.embeddings().create(input=text)
            if "data" in response and len(response["data"]) > 0:
                return response["data"][0]["embedding"]
            return []
        else:
            # For OpenAI, use the standard API
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
    except Exception as e:
        import logging
        logging.error(f"Error generating embedding: {e}")
        # Return empty embedding on error
        return []


def get_embedding_with_cache(text, doc_id=None, chunk_index=None):
    """
    Generate or retrieve a cached embedding for the given text.
    Uses SHA-256(document_id + chunk_index) or SHA-256(text) to cache embeddings.
    
    Args:
        text (str): Text to embed
        doc_id (str, optional): Document ID
        chunk_index (int, optional): Chunk index within document
        
    Returns:
        list: Vector embedding
    """
    from django.conf import settings
    import redis
    import json
    
    # Initialize Redis connection
    try:
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
    except Exception as e:
        print(f"Warning: Could not connect to Redis for embedding cache: {e}")
        return generate_embedding(text)
    
    # Generate a cache key
    if doc_id and chunk_index is not None:
        # Use document_id + chunk_index if provided
        cache_key = f"embedding:{doc_id}_{chunk_index}"
        hash_key = hashlib.sha256(cache_key.encode()).hexdigest()
    else:
        # Otherwise use the text content itself
        # This is fine for relatively short text, but for very long text,
        # you might want to hash only the first N characters
        text_for_hash = text[:1000] if len(text) > 1000 else text
        hash_key = hashlib.sha256(text_for_hash.encode()).hexdigest()
        cache_key = f"embedding:text_{hash_key}"
    
    # Try to get cached embedding
    try:
        cached_embedding = redis_client.get(cache_key)
        if cached_embedding:
            return json.loads(cached_embedding)
    except Exception as e:
        print(f"Warning: Error retrieving embedding from cache: {e}")
    
    # If no cached embedding, generate a new one
    embedding = generate_embedding(text)
    
    # Cache the embedding with a 30-day TTL
    try:
        if embedding:
            redis_client.setex(
                cache_key,
                60 * 60 * 24 * 30,  # 30 days in seconds
                json.dumps(embedding)
            )
    except Exception as e:
        print(f"Warning: Could not cache embedding: {e}")
    
    return embedding


def add_document_chunk_to_weaviate(content, metadata):
    """
    Add a document chunk to Weaviate with its embedding.
    Uses caching to avoid redundant embedding generation.
    
    Args:
        content (str): Text content of the chunk
        metadata (dict): Metadata for the chunk (doc_type, title, author, etc.)
        
    Returns:
        str: UUID of the created object
    """
    client = get_weaviate_client()
    
    # Generate embedding using cache system
    # Use metadata to create a unique cache key
    doc_id = f"{metadata.get('doc_type', 'unknown')}_{metadata.get('title', 'untitled')}"
    chunk_index = metadata.get('chapter', '0')
    embedding = get_embedding_with_cache(content, doc_id, chunk_index)
    
    if not embedding:
        print("Warning: Failed to generate embedding, skipping chunk")
        return None
        
    # Apply differential privacy protection if enabled
    if getattr(settings, 'ENABLE_DP_EMBEDDING_PROTECTION', False):
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        embedding = protect_embedding_deterministic(embedding, doc_id, content_hash)
    
    # Prepare data object
    data_object = {
        "content": content,
        **metadata
    }
    
    # Add to Weaviate
    try:
        result = client.data_object.create(
            class_name="Document",
            data_object=data_object,
            vector=embedding
        )
        return result
    except Exception as e:
        print(f"Error adding document to Weaviate: {e}")
        return None


def add_figure_to_weaviate(figure_data):
    """
    Add a figure to Weaviate with its embedding.
    Uses caption text for embedding generation.
    
    Args:
        figure_data (dict): Figure data including caption, figure_id, metadata, etc.
        
    Returns:
        str: UUID of the created object
    """
    client = get_weaviate_client()
    
    # The caption is the primary text to embed
    caption = figure_data.get("caption", "")
    if not caption:
        print("Warning: Figure has no caption, using empty string")
    
    # Generate embedding from caption
    figure_id = figure_data.get("figure_id", "unknown")
    embedding = get_embedding_with_cache(caption, f"figure_{figure_id}")
    
    if not embedding:
        print(f"Warning: Failed to generate embedding for figure {figure_id}")
        return None
    
    # Add to Weaviate
    try:
        result = client.data_object.create(
            class_name="Figure",
            data_object=figure_data,
            vector=embedding
        )
        return result
    except Exception as e:
        print(f"Error adding figure to Weaviate: {e}")
        return None


def search_weaviate(query_text, doc_type=None, limit=10, use_hybrid=True, alpha=0.75, 
                 collection="Document", include_figures=False, filters=None):
    """
    Search for relevant document chunks or figures in Weaviate.
    
    Args:
        query_text (str): The query text
        doc_type (str, optional): Filter by document type
        limit (int, optional): Maximum number of results to return
        use_hybrid (bool, optional): Whether to use hybrid search (vector + keyword)
        alpha (float, optional): Weight for vector search in hybrid mode (0-1)
            Higher values favor vector similarity over keyword matching
        collection (str, optional): Which collection to search ("Document" or "Figure")
        include_figures (bool, optional): Whether to include figures in the results
            Only applies when collection="Document"
        filters (dict, optional): Advanced filter criteria
        
    Returns:
        list: List of relevant document chunks or figures with metadata
    """
    # Import locally to avoid circular imports
    import time
    try:
        from ..analytics.collectors import MetricsCollector
        metrics_available = True
    except ImportError:
        metrics_available = False
    client = get_weaviate_client()
    results = []
    
    # Start timing for analytics
    start_time = time.time()
    total_documents_searched = 0
    
    # Search Document collection
    if collection == "Document" or include_figures:
        # Build query for Document collection
        if use_hybrid:
            # Hybrid search (vector + BM25)
            query = (
                client.query
                .get("Document", ["content", "doc_type", "title", "author", "year", "chapter", "source"])
                .with_hybrid(
                    query=query_text,
                    alpha=alpha,  # Weight for vector search (0.75 = 75% vector, 25% keyword)
                    properties=["content"]  # Only search content field for keywords
                )
                .with_limit(limit)
            )
        else:
            # Vector-only search
            query = (
                client.query
                .get("Document", ["content", "doc_type", "title", "author", "year", "chapter", "source"])
                .with_near_text({"concepts": [query_text]})
                .with_limit(limit)
            )
        
        # Add filter if specified
        if filters:
            query = query.with_where(filters)
        # Add simple doc_type filter if specified and no advanced filters
        elif doc_type:
            query = query.with_where({
                "path": ["doc_type"],
                "operator": "Equal",
                "valueString": doc_type
            })
        
        # Execute query
        try:
            query_results = query.do()
            documents = query_results.get("data", {}).get("Get", {}).get("Document", [])
            results.extend(documents)
        except Exception as e:
            print(f"Error searching Document collection: {e}")
    
    # Search Figure collection if requested or it's the specified collection
    if collection == "Figure" or (include_figures and collection == "Document"):
        # Figure search limit
        fig_limit = limit // 2 if collection == "Document" else limit
        
        # Build query for Figure collection
        if use_hybrid:
            # Hybrid search using caption field
            fig_query = (
                client.query
                .get("Figure", ["figure_id", "figure_type", "caption", "page_number", 
                                "file_path", "doc_type", "title", "author", "year"])
                .with_hybrid(
                    query=query_text,
                    alpha=alpha,
                    properties=["caption"]
                )
                .with_limit(fig_limit)
            )
        else:
            # Vector-only search
            fig_query = (
                client.query
                .get("Figure", ["figure_id", "figure_type", "caption", "page_number", 
                                "file_path", "doc_type", "title", "author", "year"])
                .with_near_text({"concepts": [query_text]})
                .with_limit(fig_limit)
            )
        
        # Add filter if specified
        if filters:
            # For figures, we might need to modify the filter paths
            figure_filters = _adapt_filters_for_figure_collection(filters)
            fig_query = fig_query.with_where(figure_filters)
        # Add simple doc_type filter if specified and no advanced filters
        elif doc_type:
            fig_query = fig_query.with_where({
                "path": ["doc_type"],
                "operator": "Equal",
                "valueString": doc_type
            })
        
        # Execute query
        try:
            fig_results = fig_query.do()
            figures = fig_results.get("data", {}).get("Get", {}).get("Figure", [])
            
            # If we're mixing Documents and Figures, mark the type
            if collection == "Document" and include_figures:
                for figure in figures:
                    figure["result_type"] = "figure"
                
                # Mark document results as well
                for doc in results:
                    doc["result_type"] = "document"
            
            results.extend(figures)
        except Exception as e:
            print(f"Error searching Figure collection: {e}")
    
    # Record metrics for vector search if available
    if metrics_available:
        elapsed_ms = (time.time() - start_time) * 1000
        try:
            MetricsCollector.record_vector_search_time(
                collection=collection,
                num_vectors=total_documents_searched,
                top_k=limit,
                time_ms=elapsed_ms,
                metadata={
                    'use_hybrid': use_hybrid,
                    'alpha': alpha if use_hybrid else None,
                    'include_figures': include_figures,
                    'doc_type': doc_type,
                    'has_advanced_filters': filters is not None,
                    'results_count': len(results)
                }
            )
        except Exception as e:
            # Don't let metrics failure affect the search results
            print(f"Error recording vector search metrics: {e}")
    
    return results


def _adapt_filters_for_figure_collection(filters):
    """
    Adapt document filters for use with the Figure collection.
    Some field paths may be different between collections.
    
    Args:
        filters (dict): Filter object for Document collection
        
    Returns:
        dict: Adapted filter object for Figure collection
    """
    # If filters is None or empty, return as is
    if not filters:
        return filters
        
    # Make a deep copy to avoid modifying the original
    import copy
    adapted_filters = copy.deepcopy(filters)
    
    # Helper function to recursively modify paths in filters
    def adapt_paths(filter_obj):
        if isinstance(filter_obj, dict):
            # If it's a filter operation with a path
            if "path" in filter_obj and "operator" in filter_obj:
                # The field mappings between Document and Figure collections
                field_mapping = {
                    # Add mappings here if fields have different names
                    # e.g., "document_content": "caption",
                }
                
                # Update path if it's in our mapping
                path = filter_obj["path"]
                if isinstance(path, list) and path and path[0] in field_mapping:
                    filter_obj["path"] = [field_mapping[path[0]]] + path[1:]
                    
            # Process all other dictionary values
            for key, value in filter_obj.items():
                if isinstance(value, (dict, list)):
                    adapt_paths(value)
        
        # If it's a list (e.g., operands), process each item
        elif isinstance(filter_obj, list):
            for item in filter_obj:
                adapt_paths(item)
    
    # Apply the adaptations
    adapt_paths(adapted_filters)
    
    return adapted_filters