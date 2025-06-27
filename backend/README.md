# RNA Lab Navigator - Backend

This is the Django backend for the RNA Lab Navigator, a retrieval-augmented generation (RAG) system for RNA biology research.

## 🚀 Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## 📁 Directory Structure

```
backend/
├── api/                    # Main API application
│   ├── chat/              # Chat interface with enhanced context
│   ├── ingestion/         # Document processing and vectorization
│   ├── rag/               # RAG implementation with Weaviate
│   ├── search/            # Search functionality
│   ├── security/          # Security middleware and features
│   └── intelligence/      # Advanced AI features
├── rna_backend/           # Django project settings
├── scripts/               # Utility scripts
├── tests/                 # Test suite
└── manage.py             # Django management script
```

## 🔑 Key Features

- **Enhanced RAG Pipeline**: Production-ready Weaviate integration
- **Intelligent Suggestions**: Context-aware follow-up questions
- **Conversation Coherence**: Pronoun resolution and topic tracking
- **Security**: GMP-level compliance features
- **Performance**: Optimized for <15s response times

## 🛠️ Core Components

### 1. RAG System (`api/rag/`)
- `weaviate_production_rag.py`: Main RAG implementation
- `production_integration.py`: Integration layer with caching
- `enhanced_context.py`: Advanced conversation management

### 2. Document Ingestion (`api/ingestion/`)
- `ingest_thesis.py`: Process PhD theses
- `chunking_utils.py`: 400±50 word chunks with 100-word overlap
- `embeddings_utils.py`: OpenAI Ada-002 embeddings

### 3. Chat Interface (`api/chat/`)
- Context window: 10 messages
- Pronoun resolution
- Topic tracking
- Conversation summarization

## 🔐 Security Features

- PII detection and filtering
- Rate limiting
- CORS configuration
- JWT authentication (planned)
- Audit logging

## 🧪 Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test tests.test_rag_smoke

# Run with coverage
pytest --cov=api tests/
```

## 🐳 Docker Support

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## 📊 Database

- **PostgreSQL**: Main database
- **Weaviate**: Vector database (2,438+ vectors)
- **Redis**: Caching and Celery broker

## 🔧 Celery Tasks

```bash
# Start worker
celery -A rna_backend worker -l info

# Start beat scheduler
celery -A rna_backend beat -l info
```

## 🚀 Deployment

The backend is configured for deployment on Railway. See `railway.json` for configuration.

## 📝 API Documentation

API endpoints are available at:
- `/api/chat/` - Chat interface
- `/api/search/` - Document search
- `/api/ingestion/` - Document upload

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## 📞 Support

For issues or questions, contact the RNA Lab Navigator team.