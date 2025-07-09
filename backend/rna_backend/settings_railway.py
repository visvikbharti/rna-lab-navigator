"""
Railway-specific settings that work without heavy ML dependencies
"""
from .settings_production import *

# Disable local ML models for Railway deployment
ENABLE_LOCAL_EMBEDDINGS = False
ENABLE_CROSS_ENCODER = False
ENABLE_OFFLINE_MODE = False

# Use OpenAI for all embeddings
USE_OPENAI_EMBEDDINGS = True

# Simplified search without ML ranking
USE_SIMPLE_SEARCH = True

# Disable features that require sentence-transformers
ENABLE_SEMANTIC_SEARCH = False
ENABLE_HYBRID_SEARCH = False

# Use basic BM25 search only
DEFAULT_SEARCH_METHOD = 'keyword'

# Reduce memory usage
RAG_MAX_CONTEXT_CHUNKS = 3
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

print("Using Railway-optimized settings without heavy ML dependencies")