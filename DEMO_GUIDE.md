# RNA Lab Navigator Demo Guide

This guide provides step-by-step instructions for getting the RNA Lab Navigator demo up and running on your local system.

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 18+
- OpenAI API key

## Setup Instructions

### 1. Run the Automated Setup Script

The easiest way to set up the demo is by running the provided setup script:

```bash
# Make the script executable if needed
chmod +x scripts/setup_demo.sh

# Run the setup script
./scripts/setup_demo.sh
```

This script will:
- Create and configure necessary environment files
- Start Docker services (PostgreSQL, Redis, Weaviate)
- Set up the backend Python environment
- Configure the frontend environment
- Create an admin user for the Django admin interface

**IMPORTANT**: You must provide your OpenAI API key during this setup. The script will prompt you to edit the `.env` file.

### 2. Ingest Sample Documents

Once the setup is complete, ingest the sample documents provided in the `data/sample_docs` directory:

```bash
# Activate the Python virtual environment
cd backend
source venv/bin/activate

# Run the ingestion script (--purge removes any existing data)
python ../scripts/ingest_sample_docs.py --purge
```

This will process:
- Thesis documents
- Protocol PDFs
- Research papers
- Troubleshooting guides

### 3. Start the Services

You'll need to open three terminal windows to run all components:

#### Terminal 1: Django Backend
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

#### Terminal 2: Celery Worker
```bash
cd backend
source venv/bin/activate
celery -A rna_backend worker -l info
```

#### Terminal 3: Frontend
```bash
cd frontend
npm run dev
```

### 4. Access the Application

- Frontend UI: http://localhost:5173/
- API Endpoints: http://localhost:8000/api/
- Admin Interface: http://localhost:8000/admin/ (login with username: `admin`, password: `admin123`)

## Sample Queries to Try

Test the system with these example queries:

- "What's the protocol for RNA extraction using TRIzol?"
- "How does CRISPR-Cas9 work for diagnostic applications?"
- "What did Phutela's thesis conclude about RNA processing?"
- "What are common issues with Western blot and how to solve them?"

## Troubleshooting

### Common Issues

- **OpenAI API errors**: Verify your API key is correctly set in both `.env` files
- **Weaviate connection errors**: Ensure Docker services are running (`docker ps`)
- **Frontend proxy errors**: Confirm the backend server is running on port 8000
- **Empty search results**: Check if document ingestion completed successfully

### Logs

Check logs for more detailed error information:

- Backend logs: Terminal 1 output
- Celery worker logs: Terminal 2 output
- Docker container logs: `docker logs rna_weaviate` (or postgres/redis)

## Next Steps

Explore the detailed documentation in the `docs/` directory for more information on:

- [User Guide](docs/user_guide/index.md)
- [API Reference](docs/api_reference/index.md)
- [Developer Guide](docs/developer_guide/index.md)
- [Deployment Guide](docs/deployment_guide.md)
- [Integration Examples](docs/integration_examples.md)