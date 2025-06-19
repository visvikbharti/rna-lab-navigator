# RNA Lab Navigator - Deployment Reference

## Original Project and Deployment Information

This document serves as a reference for the deployment setup of the RNA Lab Navigator project, working from the original project directory.

### Directory Structure

- **Original Project Directory:** `/Users/vishalbharti/Downloads/rna-lab-navigator`
- **Deployment Repository Directory:** `/Users/vishalbharti/Downloads/rna-lab-deploy`
- **GitHub Repository:** https://github.com/visvikbharti/rna-lab-deploy

### Key Files in Original Project

1. **Dockerfile**
   - Located at: `/Users/vishalbharti/Downloads/rna-lab-navigator/backend/Dockerfile`
   - Purpose: Defines the container image for the backend service
   - Used as reference for the deployment repository

2. **docker-entrypoint.sh**
   - Located at: `/Users/vishalbharti/Downloads/rna-lab-navigator/backend/docker-entrypoint.sh`
   - Purpose: Original script for initializing the application
   - Copied and modified for deployment

3. **Original Railway Configuration**
   - Located at: `/Users/vishalbharti/Downloads/rna-lab-navigator/backend/railway.json`
   - Purpose: Provides a template for Railway configuration

### Environment Variables

The environment variables from the original project are defined in:
- `/Users/vishalbharti/Downloads/rna-lab-navigator/backend/.env`
- `/Users/vishalbharti/Downloads/rna-lab-navigator/backend/.env.production`

These have been transferred to Railway environment variables without exposing sensitive keys.

### Project Architecture

As defined in `CLAUDE.md`:

- **Backend**: Django 4 + DRF + Celery → `backend/`
- **Frontend**: React 18 + Vite + Tailwind → `frontend/`
- **Vector DB**: Weaviate (HNSW + BM25 hybrid)
- **LLM**: OpenAI GPT-4o for answers, Ada-002 for embeddings
- **Infra**: Docker (Postgres | Redis | Weaviate), deployed on Railway

### Deployment Strategy

1. Created a clean GitHub repository without sensitive information
2. Set up three services on Railway:
   - PostgreSQL (managed by Railway)
   - Redis (managed by Railway)
   - Backend (deployed from GitHub)
3. Connected the services through environment variables
4. Added necessary configuration files and scripts

### Deployment Files in Deployment Repository

These files were created/modified in the deployment repository:

1. **docker-entrypoint.sh**
   - Added PostgreSQL connection check
   - Configured to run migrations and collect static files

2. **railway.json**
   - Added healthcheck configuration
   - Set appropriate restart policies
   - Configured the correct start command

3. **DEPLOYMENT_GUIDE.md**
   - Comprehensive guide for the deployment process

### Railway Setup

The Railway project is configured with:

1. **Backend Service**
   - Root Directory: `backend`
   - Start Command: `/app/docker-entrypoint.sh`
   - Health Check Path: `/api/health/`
   - Connected to PostgreSQL and Redis

2. **Environment Variables**
   - Essential variables set in the Railway console
   - Database and Redis connection details shared between services

### Next Steps

1. Complete backend deployment
2. Deploy the frontend service
3. Set up Weaviate for vector storage
4. Configure Celery workers for background tasks

### Reference Commands

```bash
# Copy files from original to deployment repo
cp /Users/vishalbharti/Downloads/rna-lab-navigator/backend/Dockerfile /Users/vishalbharti/Downloads/rna-lab-deploy/backend/

# Push changes to deployment repo
git -C /Users/vishalbharti/Downloads/rna-lab-deploy add .
git -C /Users/vishalbharti/Downloads/rna-lab-deploy commit -m "Your commit message"
git -C /Users/vishalbharti/Downloads/rna-lab-deploy push origin main

# Check deployment status
# Visit Railway dashboard at https://railway.app/dashboard
```

### Important Notes

- Sensitive information like API keys must only be configured through Railway's environment variables, never committed to the repository
- Always check deployment logs on Railway for troubleshooting
- The health check endpoint at `/api/health/` is essential for monitoring deployment status

For more detailed information, refer to the comprehensive guide in the deployment repository: `/Users/vishalbharti/Downloads/rna-lab-deploy/DEPLOYMENT_GUIDE.md`