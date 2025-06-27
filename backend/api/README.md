# RNA Lab Navigator - API Module

Core API functionality for the RNA Lab Navigator system.

## 📁 Module Structure

```
api/
├── chat/              # Chat interface and conversation management
├── ingestion/         # Document processing and vectorization
├── rag/               # Retrieval-Augmented Generation pipeline
├── search/            # Search functionality and ranking
├── security/          # Security middleware and authentication
├── intelligence/      # Advanced AI features (knowledge graphs, gaps)
├── feedback/          # User feedback system
├── analytics/         # Usage analytics and monitoring
└── agents/           # Multi-agent system (planned)
```

## 🔑 Core Modules

### Chat Module (`chat/`)
Handles conversational interactions with enhanced context awareness.

**Key files:**
- `views.py`: Main chat endpoints
- `enhanced_context.py`: Pronoun resolution and topic tracking
- `models.py`: ChatSession and ChatMessage models

**Features:**
- 10-message context window
- Conversation summarization
- Topic detection
- Reference resolution

### Ingestion Module (`ingestion/`)
Processes documents and creates vector embeddings.

**Key files:**
- `ingest_thesis.py`: PhD thesis processor
- `chunking_utils.py`: Text chunking (400±50 words)
- `embeddings_utils.py`: OpenAI embeddings

**Supported formats:**
- PDF (papers, theses, protocols)
- CSV (reagent lists)
- DOCX (via conversion)

### RAG Module (`rag/`)
Production-ready RAG implementation with Weaviate.

**Key files:**
- `weaviate_production_rag.py`: Main RAG class
- `production_integration.py`: Integration layer
- `enhanced_rag.py`: Advanced features

**Performance:**
- Response time: 10-15s
- Cached responses: <1s
- Confidence scoring: 0.45-0.95

### Search Module (`search/`)
Hybrid search with BM25 and vector similarity.

**Key files:**
- `real_rag.py`: Search implementation
- `hybrid_search.py`: Combined search strategy
- `reranking.py`: Result reranking

### Security Module (`security/`)
Enterprise-grade security features.

**Components:**
- PII detection and filtering
- Rate limiting
- WAF (Web Application Firewall)
- Audit logging
- JWT authentication (planned)

## 🔌 API Endpoints

### Chat Endpoints
- `POST /api/chat/sessions/` - Create chat session
- `POST /api/chat/sessions/{id}/messages/` - Send message
- `GET /api/chat/sessions/{id}/` - Get session history

### Search Endpoints
- `POST /api/search/` - Search documents
- `GET /api/search/suggestions/` - Get search suggestions

### Ingestion Endpoints
- `POST /api/ingestion/upload/` - Upload document
- `GET /api/ingestion/status/{id}/` - Check processing status

## 🔐 Authentication

Currently using session-based authentication. JWT implementation planned for:
- API key management
- Role-based access control
- Audit trails

## 📊 Response Format

All API responses follow this structure:
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message",
  "metadata": {
    "processing_time": 0.123,
    "confidence_score": 0.85
  }
}
```

## 🧪 Testing

Each module has its own test suite:
```bash
python manage.py test api.chat
python manage.py test api.rag
python manage.py test api.search
```

## 🚀 Performance Considerations

1. **Caching**: Redis cache for embeddings and results
2. **Async Processing**: Celery for long-running tasks
3. **Connection Pooling**: Efficient database connections
4. **Rate Limiting**: Prevents API abuse

## 📝 Adding New Features

1. Create module directory under `api/`
2. Add models in `models.py`
3. Create serializers in `serializers.py`
4. Implement views in `views.py`
5. Add URLs in `urls.py`
6. Write tests in module directory
7. Update main `api/urls.py`

## 🤝 Module Communication

Modules communicate through:
- Django signals
- Celery tasks
- Service layer methods
- Direct imports (minimize coupling)

## 📞 Support

For API development questions, refer to the main documentation or contact the development team.