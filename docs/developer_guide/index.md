# Developer Guide

Welcome to the RNA Lab Navigator developer guide. This document provides comprehensive information for developers working on maintaining, extending, or integrating with the RNA Lab Navigator system.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment Setup](#development-environment-setup)
4. [Project Structure](#project-structure)
5. [Core Components](#core-components)
6. [Extension Points](#extension-points)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Performance Optimization](#performance-optimization)
10. [Contributing](#contributing)

## Introduction

RNA Lab Navigator is a private, retrieval-augmented assistant designed for Dr. Debojyoti Chakraborty's RNA-biology lab at CSIR-IGIB. The system helps researchers find answers to protocol, thesis, and paper questions with proper citations, preserving institutional memory and accelerating experiments.

This guide is intended for developers who:
- Are maintaining the existing codebase
- Are adding new features to the system
- Need to integrate other systems with RNA Lab Navigator
- Want to understand the system architecture and design decisions

## Architecture Overview

RNA Lab Navigator follows a modern architecture with these key components:

1. **Frontend**: React 18 + Vite + Tailwind CSS
2. **Backend**: Django 4 + Django REST Framework + Celery
3. **Vector Database**: Weaviate (HNSW + BM25 hybrid search)
4. **Language Models**: OpenAI GPT-4o for answers, Ada-002 for embeddings
5. **Infrastructure**: Docker for containerization (Postgres, Redis, Weaviate)
6. **Deployment**: Railway + Vercel

The system uses a RAG (Retrieval-Augmented Generation) approach to provide accurate answers:
1. User query → API → Backend
2. Backend searches Weaviate for relevant documents
3. Cross-encoder reranking improves result relevance
4. Selected documents are formatted into a prompt
5. LLM generates an answer with citations
6. Answer and sources are returned to the user

### High-Level Data Flow

```
┌────────┐     ┌────────┐     ┌────────────┐     ┌──────────┐
│Document│────▶│Chunking│────▶│Embedding   │────▶│Weaviate  │
│Ingestion│     │Pipeline│     │Generation  │     │Vector DB │
└────────┘     └────────┘     └────────────┘     └──────────┘
                                                       │
┌────────┐     ┌────────┐     ┌────────────┐          │
│Frontend│◀───▶│Backend │◀───▶│Query       │◀─────────┘
│UI      │     │API     │     │Processing  │
└────────┘     └────────┘     └────────────┘
                                     │
                                     ▼
                              ┌────────────┐
                              │OpenAI API  │
                              │LLM Services│
                              └────────────┘
```

## Development Environment Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker and Docker Compose
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/rna-lab-navigator.git
cd rna-lab-navigator
```

### Step 2: Environment Setup

Create and configure environment files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Edit the `.env` files to include your API keys and configuration values.

### Step 3: Start Services with Docker

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (persistent storage)
- Redis (caching and Celery broker)
- Weaviate (vector database)

### Step 4: Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Step 5: Start Celery Workers

In new terminal windows:

```bash
# Terminal 1
cd backend
source venv/bin/activate
celery -A rna_backend worker -l info

# Terminal 2
cd backend
source venv/bin/activate
celery -A rna_backend beat -l info
```

### Step 6: Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Step 7: Load Sample Data

```bash
cd backend
python api/ingestion/ingest_thesis.py ../data/sample_docs/theses/2025_Phutela_Rhythm_PhD_Thesis.pdf "Rhythm Phutela" 2025
```

## Project Structure

The RNA Lab Navigator codebase is organized as follows:

```
rna-lab-navigator/
│
├── backend/                 # Django backend
│   ├── api/                 # Main API app
│   │   ├── ingestion/       # Document ingestion components
│   │   ├── auth/            # Authentication components
│   │   ├── analytics/       # Analytics and monitoring
│   │   ├── security/        # Security components
│   │   ├── rag/             # RAG pipeline components
│   │   ├── search/          # Enhanced search features
│   │   ├── llm/             # LLM integration components
│   │   ├── quality/         # Quality control components 
│   │   ├── offline/         # Offline mode components
│   │   ├── backup/          # Backup system
│   │   └── models.py        # Core data models
│   └── rna_backend/         # Django project configuration
│
├── frontend/                # React frontend
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── api/             # API integration
│   │   ├── hooks/           # Custom React hooks
│   │   └── utils/           # Utility functions
│   └── public/              # Static assets
│
├── data/                    # Sample data for development
│   └── sample_docs/         # Sample documents for testing
│
├── docs/                    # Documentation
│   ├── user_guide/          # End-user documentation
│   ├── api_reference/       # API documentation
│   └── developer_guide/     # Developer documentation
│
├── docker-compose.yml       # Docker Compose configuration
├── docker-compose.prod.yml  # Production Docker configuration
└── .github/                 # GitHub Actions workflows
```

## Core Components

### 1. Document Ingestion

Located in `backend/api/ingestion/`, this component handles:
- Document parsing and text extraction
- Chunking documents into manageable pieces
- Generating embeddings for vector search
- Storing documents and metadata in Weaviate

Key files:
- `chunking_utils.py`: Splits documents into chunks
- `embeddings_utils.py`: Generates embeddings and interfaces with Weaviate
- `ingest_thesis.py`: Specialized ingestion for thesis documents

### 2. RAG Pipeline

Located in `backend/api/views.py` and related modules, the RAG pipeline:
- Processes user queries
- Searches for relevant documents
- Reranks search results
- Formats prompts for the LLM
- Generates answers with citations
- Calculates confidence scores

Key components:
- `QueryView`: Main entry point for the RAG pipeline
- `rerank_results()`: Improves search result relevance
- `build_prompt()`: Formats context for the LLM
- `calculate_confidence_score()`: Assesses answer quality

### 3. Frontend Components

Located in `frontend/src/components/`, these provide the user interface:
- `ChatBox.jsx`: Main interface for conversational interaction
- `AnswerCard.jsx`: Displays answers with citations
- `FilterChips.jsx`: Allows filtering by document type
- `ProtocolUploader.jsx`: Enables users to upload new protocols

### 4. Security Components

Located in `backend/api/security/`, these implement:
- Authentication and authorization
- Rate limiting
- Input validation
- Audit logging
- mTLS for secure communication
- Network isolation controls

### 5. Analytics System

Located in `backend/api/analytics/`, this tracks:
- Query volume and patterns
- Response times
- User feedback
- Model performance metrics
- Cost monitoring

## Extension Points

RNA Lab Navigator is designed with multiple extension points to facilitate customization and enhancement:

### 1. Document Types

To add support for a new document type:
1. Create a new ingestion module in `backend/api/ingestion/`
2. Implement specialized chunking logic if needed
3. Update the UI to support the new document type

### 2. Vector Database Providers

The system can be extended to support alternative vector databases:
1. Create a new adapter class in `backend/api/offline/`
2. Implement the required interface methods
3. Update configuration to use the new adapter

### 3. Language Models

To add support for alternative language models:
1. Extend the LLM client factory in `backend/api/offline/__init__.py`
2. Implement the required formatting for the new model
3. Update model selection logic in `QueryView.select_model()`

### 4. Custom Plugins

The system supports plugins for specialized functionality:
1. Create a new Django app in the backend
2. Implement the plugin interface
3. Register the plugin in settings
4. Expose new API endpoints as needed

## Testing

RNA Lab Navigator includes comprehensive testing infrastructure:

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Test Types

1. **Unit Tests**: Test individual components in isolation
   - Located in `backend/tests/test_unit/`
   - Test individual functions and classes

2. **Integration Tests**: Test component interactions
   - Located in `backend/tests/test_integration/`
   - Test the RAG pipeline end-to-end

3. **API Tests**: Test API endpoints
   - Located in `backend/tests/test_api/`
   - Test request validation and responses

4. **Performance Tests**: Test system performance
   - Located in `backend/tests/test_performance/`
   - Test query response times and resource usage

5. **Security Tests**: Test security measures
   - Located in `backend/tests/test_security/`
   - Test authentication, authorization, and input validation

### Writing Tests

When adding new features, always include tests:
1. Create a new test file in the appropriate directory
2. Use pytest fixtures for setup and teardown
3. Mock external services to avoid network calls
4. Test both success and failure cases
5. Include performance and security tests for critical components

## Deployment

RNA Lab Navigator can be deployed in several ways:

### Railway Deployment (Backend)

```bash
railway up
```

This deploys the Django backend, including:
- Database migrations
- Static files
- API endpoints
- Celery workers

### Vercel Deployment (Frontend)

```bash
cd frontend
vercel --prod
```

This deploys the React frontend to Vercel.

### Self-Hosted Deployment

For air-gapped environments or custom hosting:

1. Build Docker images:
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. Deploy services:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. Configure Nginx for reverse proxy:
   ```
   server {
       listen 80;
       server_name your-domain.com;
       
       location /api/ {
           proxy_pass http://backend:8000;
           # Additional proxy settings
       }
       
       location / {
           root /usr/share/nginx/html;
           # Frontend static files
       }
   }
   ```

## Performance Optimization

For optimal performance, consider these strategies:

### 1. Query Optimization

- Enable query caching for frequently asked questions
- Adjust chunking parameters based on document type
- Optimize hybrid search parameters (alpha value)
- Use cross-encoder reranking selectively

### 2. Database Optimization

- Configure proper indexes in PostgreSQL
- Adjust Weaviate vector indexing parameters
- Implement sharding for large document collections
- Set up database query caching

### 3. Frontend Optimization

- Implement client-side caching
- Use code splitting to reduce bundle size
- Optimize React rendering (useMemo, useCallback)
- Implement progressive loading for large result sets

### 4. LLM Cost Management

- Implement tiered model selection based on query complexity
- Cache LLM responses for common queries
- Optimize prompt design to reduce token usage
- Monitor and limit API usage based on budget

## Contributing

We welcome contributions to RNA Lab Navigator. Please follow these guidelines:

### Code Style

- Backend: PEP 8 style guide, enforced with Black and isort
- Frontend: Prettier for JavaScript/JSX formatting

### Development Workflow

1. Create a feature branch from `master`
2. Implement your changes with tests
3. Follow the commit message convention
4. Submit a pull request with a clear description
5. Address review feedback

### Documentation

When making changes:
1. Update inline code documentation
2. Update user documentation if UI changes
3. Update API documentation if endpoints change
4. Update this developer guide for architectural changes

### Code Review Process

All contributions undergo code review:
1. Automated checks (linting, tests)
2. Peer review for code quality
3. Security review for sensitive changes
4. Performance review for critical components

## Troubleshooting

Common issues and solutions:

### Vector Database Connection Issues

If you encounter problems connecting to Weaviate:
1. Check Docker container status: `docker ps`
2. Verify Weaviate is running: `curl http://localhost:8080/v1/meta`
3. Check for mTLS certificate issues if enabled
4. Review logs: `docker logs weaviate`

### Celery Worker Issues

If Celery tasks are not processing:
1. Check Redis connection: `redis-cli ping`
2. Verify workers are running: `celery -A rna_backend status`
3. Check for task errors in logs
4. Restart workers if needed

### LLM Integration Issues

If LLM responses are failing:
1. Verify API keys in environment variables
2. Check for rate limiting or quota issues
3. Test with curl to isolate backend vs. API issues
4. Check network connectivity (especially in isolated mode)