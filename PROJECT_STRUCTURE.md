# RNA Lab Navigator - Project Structure

## Overview
RNA Lab Navigator is an AI-powered research intelligence platform for Dr. Chakraborty's RNA biology lab at CSIR-IGIB. It provides instant answers to research questions with citations, automated paper monitoring, and intelligent research assistance.

## Directory Structure

```
rna-lab-navigator/
├── backend/                    # Django backend
│   ├── api/                   # Main API app
│   │   ├── agents/           # Multi-agent AI system
│   │   ├── chat/             # Chat interface backend
│   │   ├── experiments/      # Experiment mapping
│   │   ├── hypothesis/       # Hypothesis generation
│   │   ├── ingestion/        # Document processing
│   │   ├── intelligence/     # Research intelligence
│   │   ├── knowledge_graph/  # Knowledge graph
│   │   ├── llm/             # LLM integration
│   │   ├── papers/          # Paper monitoring
│   │   ├── protocols/       # Protocol generation
│   │   ├── rag/             # Enhanced RAG system
│   │   ├── search/          # Search functionality
│   │   └── websocket/       # Real-time features
│   ├── rna_backend/          # Django settings
│   ├── requirements.txt      # Python dependencies
│   └── manage.py            # Django CLI
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── api/             # API client modules
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts
│   │   ├── hooks/           # Custom hooks
│   │   ├── pages/           # Page components
│   │   ├── styles/          # CSS files
│   │   ├── utils/           # Utility functions
│   │   ├── App.jsx          # Main app component
│   │   └── main.jsx         # Entry point
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
│
├── docs/                     # Documentation
│   ├── archive/             # Archived docs
│   └── reference/           # Reference docs
│
├── data/                    # Data files
│   └── sample_docs/         # Sample documents
│
├── docker-compose.yml       # Docker services
├── README.md               # Project README
├── CLAUDE.md               # AI assistant instructions
└── entry_guide.md          # Developer guide
```

## Key Features

1. **Enhanced RAG System** - Multi-hop reasoning with conversation memory
2. **Multi-Agent AI** - 5 specialized research agents working in parallel
3. **Chat Interface** - Claude/ChatGPT-like conversational UI
4. **Paper Monitoring** - Automated bioRxiv monitoring with AI summaries
5. **Knowledge Graph** - Real-time visualization of research connections
6. **Hypothesis Explorer** - AI-powered hypothesis generation and validation
7. **Protocol Builder** - Intelligent protocol design from hypotheses
8. **Experiment Mapper** - Visualize experimental relationships

## Essential Documentation

- `README.md` - User-facing documentation
- `CLAUDE.md` - Instructions for Claude AI
- `entry_guide.md` - Developer onboarding guide
- `DEMO_GUIDE.md` - Demo walkthrough
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `FEATURE_UPDATE_SUMMARY.md` - Latest features

## Technology Stack

- **Backend**: Django 4, DRF, Celery, Redis
- **Frontend**: React 18, Vite, Tailwind CSS
- **Vector DB**: Weaviate
- **LLM**: OpenAI GPT-4o, Ada-002
- **Infrastructure**: Docker, PostgreSQL, Railway/Vercel

## Development Commands

```bash
# Backend
cd backend
docker-compose up -d
make dev
celery -A rna_backend worker -l info
celery -A rna_backend beat -l info

# Frontend
cd frontend
npm install
npm run dev
```

## Testing
- Backend tests: `pytest` in backend/tests/
- Frontend: Access http://localhost:5173

## Deployment
- Backend: Railway (`railway up`)
- Frontend: Vercel (`vercel --prod`)