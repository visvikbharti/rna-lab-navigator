# 🧬 RNA Lab Navigator

> **AI-Powered Research Intelligence Platform for RNA Biology**  
> Built for Dr. Debojyoti Chakraborty's RNA Biology Lab at CSIR-IGIB

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)

## 🚀 Overview

RNA Lab Navigator is an intelligent research assistant that transforms how RNA biology labs access and utilize their collective knowledge. It provides instant, cited answers to complex research questions by leveraging advanced RAG (Retrieval-Augmented Generation) technology.

### 🎯 Key Features

- **🤖 Intelligent Q&A** - Get instant answers with citations from lab documents, papers, and protocols
- **🧪 Research Intelligence** - Receive experiment suggestions, critical questions, and novel research ideas
- **👥 Multi-Agent AI System** - Specialized agents for literature analysis, hypothesis generation, and protocol design
- **💬 Conversational Interface** - Chat-like interface with context awareness and session memory
- **📊 Knowledge Graph** - Visualize connections between experiments, papers, and concepts
- **🔔 Paper Monitoring** - Automated daily scanning of bioRxiv for relevant preprints
- **🔬 Hypothesis Explorer** - AI-powered hypothesis validation and experimental design
- **📋 Protocol Builder** - Generate detailed protocols from research questions

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
│  │ Enhanced RAG │  │ Multi-Agent  │  │  Paper Monitor     │     │
│  │   Pipeline   │  │    System    │  │    (Celery)        │     │
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
- **[API Documentation](docs/api_reference.md)** - REST API endpoints and usage
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project

## 🧪 Usage Examples

### Basic Search Query
```python
POST /api/query/
{
  "query": "What is the optimal RNA extraction protocol for liver tissue?",
  "doc_type": "protocol"
}
```

### Enhanced RAG Query with Intelligence
```python
POST /api/query/enhanced/
{
  "query": "How does ERBB4 signaling affect DNA damage response?",
  "session_id": "unique-session-id"
}
```

Response includes:
- Detailed answer with citations
- Experiment suggestions
- Critical questions to consider
- Quick wins for immediate testing
- Warnings about potential pitfalls
- Novel research ideas

## 🔧 Configuration

### Key Settings (backend/rna_backend/settings.py)
```python
# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"  # or "gpt-3.5-turbo" for cost savings

# RAG Configuration
CHUNK_SIZE = 400  # words per chunk
CHUNK_OVERLAP = 100  # overlap between chunks
MIN_CONFIDENCE_THRESHOLD = 0.45  # minimum confidence for answers

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
```

## 📊 Performance Metrics

- **Answer Quality**: ≥85% accuracy on test questions
- **Response Time**: <5 seconds for standard queries
- **Document Support**: 10+ SOPs, theses, daily preprints
- **Concurrent Users**: 50+ supported
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Dr. Debojyoti Chakraborty and the RNA Biology Lab at CSIR-IGIB
- OpenAI for GPT-4 API
- Weaviate for vector database technology
- The open-source community

## 📞 Contact

- **Lab Website**: [RNA Biology Lab - CSIR-IGIB](https://www.igib.res.in)
- **Project Lead**: Vishal Bharti
- **Email**: vishalbharti@example.com

---

<p align="center">
  Built with ❤️ for advancing RNA biology research
</p>