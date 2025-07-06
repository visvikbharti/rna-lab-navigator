# 🧬 RNA Lab Navigator

> **AI-Powered Research Intelligence Platform for RNA Biology**  
> Built for Dr. Debojyoti Chakraborty's RNA Biology Lab at CSIR-IGIB

[![License: Private](https://img.shields.io/badge/License-Private-red.svg)]()
[![Status: Production Ready](https://img.shields.io/badge/Status-Production_Ready-green.svg)]()
[![Deployment: PythonAnywhere + Vercel](https://img.shields.io/badge/Deployment-PythonAnywhere_+_Vercel-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)

## 🚀 Overview

RNA Lab Navigator is an intelligent research assistant that transforms how RNA biology labs access and utilize their collective knowledge. It provides instant, cited answers to complex research questions by leveraging advanced RAG (Retrieval-Augmented Generation) technology.

### 🎯 Key Features

- **🤖 Intelligent Q&A** - Get instant answers with citations from 2,438+ vectors (7 PhD theses, 18 papers, 9 protocols)
- **💡 Smart Suggestions** - Context-aware follow-up questions with confidence scores (0.7-0.95)
- **🧠 Enhanced Conversation** - Pronoun resolution, topic tracking, and 10-message context window
- **💬 ChatGPT-like Interface** - Natural conversation flow with typing indicators and animations
- **🚀 Optimized Performance** - 10-15s response time with caching (<1s for cached queries)
- **🔒 Enterprise Security** - PII filtering, rate limiting, audit trails (GMP-compliant ready)
- **📊 Knowledge Coverage** - Complete lab knowledge base including all PhD theses
- **🔔 Real-time Updates** - WebSocket support for live features (planned)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │   Search     │  │     Chat     │  │   Visualization    │     │
│  │  Interface   │  │   Interface  │  │   Components       │     │
│  └─────────────┘  └──────────────┘  └────────────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                    Backend (Django + DRF)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ Production   │  │  Enhanced    │  │  Intelligent       │     │
│  │ RAG Pipeline │  │   Context    │  │  Suggestions       │     │
│  └─────────────┘  └──────────────┘  └────────────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌───────▼────────┐
│   PostgreSQL   │  │    Weaviate     │  │     Redis      │
│   (Metadata)   │  │  (Vector DB)    │  │   (Cache)      │
└────────────────┘  └─────────────────┘  └────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 4.2 + Django REST Framework
- **LLM**: OpenAI GPT-4o for answers, Ada-002 for embeddings
- **Vector Database**: Weaviate (HNSW + BM25 hybrid search)
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL / SQLite (dev)

### Frontend
- **Framework**: React 18 + Vite
- **UI**: Tailwind CSS + Framer Motion
- **State Management**: React Query
- **Components**: Custom glass-morphism design system

## 🚦 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- OpenAI API key

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/visvikbharti/rna-lab-navigator.git
cd rna-lab-navigator
```

2. **Set up environment variables**
```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your OpenAI API key and other settings
```

3. **Start services with Docker**
```bash
docker-compose up -d  # Starts PostgreSQL, Redis, Weaviate
```

4. **Set up the backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

5. **Start Celery workers** (in new terminals)
```bash
celery -A rna_backend worker -l info
celery -A rna_backend beat -l info
```

6. **Set up the frontend**
```bash
cd frontend
npm install
npm run dev
```

7. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/

## 📚 Documentation

- **[Developer Guide](docs/developer_facing_design_dossier.md)** - Detailed architecture and design decisions
- **[API Documentation](backend/api/README.md)** - REST API endpoints and usage
- **[Backend README](backend/README.md)** - Backend setup and configuration
- **[Frontend README](frontend/README.md)** - Frontend development guide
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment instructions

## 🧪 Usage Examples

### Basic Search Query
```python
POST /api/query/
{
  "query": "What is the optimal RNA extraction protocol for liver tissue?",
  "doc_type": "protocol"
}
```

### Chat Query with Context
```python
POST /api/chat/sessions/{session_id}/messages/
{
  "content": "How does ERBB4 signaling affect DNA damage response?"
}
```

Response includes:
- Detailed answer with citations
- Intelligent follow-up suggestions
- Confidence scores
- Source documents
- Processing metadata

## 🔧 Configuration

### Key Settings (backend/rna_backend/settings.py)
```python
# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"  # or "gpt-3.5-turbo" for cost savings

# RAG Configuration
CHUNK_SIZE = 400  # words per chunk (±50 tolerance)
CHUNK_OVERLAP = 100  # overlap between chunks
MIN_CONFIDENCE_THRESHOLD = 0.45  # minimum confidence for answers
CONTEXT_WINDOW = 10  # messages in conversation context

# Cache Configuration
PRODUCTION_RAG_CACHE_TTL = 3600  # 1 hour cache
EMBEDDING_CACHE_TTL = 86400  # 24 hour cache

# Security
RATE_LIMIT_ENABLED = True
PII_FILTER_ENABLED = True
WAF_ENABLED = False  # Enable for production
```

## 📊 Performance Metrics (June 27, 2025)

- **Answer Quality**: ≥85% accuracy with confidence scores 0.7-0.95
- **Response Time**: 10-15s (uncached), <1s (cached)
- **Vector Count**: 2,438 vectors across documents
- **Document Coverage**: 
  - 7 PhD theses (100% coverage)
  - 18 research papers
  - 9 lab protocols
- **Context Window**: 10 messages with topic tracking
- **Cost Efficiency**: <$30/month OpenAI costs

## 🚀 Deployment

### Production Deployment
- **Backend**: Railway or Heroku
- **Frontend**: Vercel or Netlify
- **Databases**: Railway PostgreSQL, Upstash Redis
- **Vector DB**: Weaviate Cloud

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This is a private repository for CSIR-IGIB RNA Biology Lab. All rights reserved.

## 📌 Current Implementation Status

### ✅ Working Features
- Chat interface with session management
- Intelligent suggestions with confidence scores
- Document search with hybrid retrieval (BM25 + vector)
- Document ingestion for PDFs (papers, theses, protocols)
- Conversation context with pronoun resolution
- Response caching for performance
- PII filtering and rate limiting

### 🚧 Planned Features (Not Yet Implemented)
- JWT authentication system
- Knowledge graph visualization
- Real-time WebSocket updates
- Automated paper monitoring
- Multi-agent analysis system

## 🙏 Acknowledgments

- Dr. Debojyoti Chakraborty and the RNA Biology Lab at CSIR-IGIB
- OpenAI for GPT-4 API
- Weaviate for vector database technology
- The open-source community

## 📞 Contact

- **Lab Website**: [RNA Biology Lab - CSIR-IGIB](https://www.igib.res.in)
- **Project Lead**: Vishal Bharti (Project Associate-II)
- **Email**: vishalvikashbharti@gmail.com
- **Repository**: https://github.com/visvikbharti/rna-lab-navigator

---

<p align="center">
  Built with ❤️ for advancing RNA biology research
</p>
