# RNA Lab Navigator - Deployment Next Steps

## Current Status

We've been working on deploying the RNA Lab Navigator to Railway with these key components:
- Backend (Django + DRF)
- PostgreSQL database
- Redis cache

## Deployment Repositories

- **Original Project**: `/Users/vishalbharti/Downloads/rna-lab-navigator`
- **Deployment Repository**: `/Users/vishalbharti/Downloads/rna-lab-deploy`
- **GitHub**: https://github.com/visvikbharti/rna-lab-deploy

## Issues Encountered

The primary issue we've faced is with the deployment's build process:
- Railway keeps reporting "Dockerfile 'Dockerfile' does not exist" even though the file exists in the repository
- We've tried updating the railway.json file to use the nixpacks builder instead
- The service has been failing during the build phase

## Next Steps

### Option 1: Fresh Service Setup

1. **Delete the current service** in Railway
2. **Create a new service** from scratch:
   - Go to the Railway dashboard
   - Click "New"
   - Select "GitHub Repo"
   - Choose the "rna-lab-deploy" repository
   - Set Root Directory to "backend"
   - Important: Select "Nixpacks" as the builder (not Dockerfile)
   - Set Start Command: `gunicorn rna_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120`

3. **Configure environment variables**:
   ```
   PORT=8000
   OPENAI_API_KEY=your-api-key
   OPENAI_MODEL=gpt-4o
   OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
   OPENAI_TIMEOUT=30
   SECRET_KEY=generated-secret-key
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1,*.railway.app
   CELERY_TIMEZONE=Asia/Kolkata
   ```

4. **Connect to PostgreSQL and Redis**:
   - Link the new service to the existing PostgreSQL service
   - Link the new service to the existing Redis service
   - Ensure database environment variables are properly passed

### Option 2: Modify Existing Service

If creating a new service is not preferred:

1. **Update railway.json** with a different configuration format
2. **Check Railway logs** for more specific error messages
3. **Attempt to manually trigger** a build with the correct configuration

### Frontend Deployment

After backend deployment is successful:

1. Create a new service for the frontend
2. Set Root Directory to "frontend"
3. Configure the API endpoint to point to the backend service
4. Set up environment variables like `VITE_API_URL` pointing to the backend URL

### Weaviate Setup

For vector search functionality:

1. Add a Weaviate service to Railway
2. Connect it to the backend
3. Configure the environment variables for Weaviate connection

## Prompt for Next Session

When continuing this deployment work, use the following prompt with Claude:

```
I'm continuing work on deploying the RNA Lab Navigator to Railway. We've been having issues with the build process, specifically Railway reporting "Dockerfile does not exist" even though it's present in the repository. We've tried using nixpacks instead of Dockerfile but still encountered issues.

Here's our current setup:
- Original repo: /Users/vishalbharti/Downloads/rna-lab-navigator
- Deployment repo: /Users/vishalbharti/Downloads/rna-lab-deploy
- GitHub: https://github.com/visvikbharti/rna-lab-deploy

Our plan is to:
1. Delete the current service on Railway
2. Create a fresh service using nixpacks builder instead of Dockerfile
3. Connect it to our existing PostgreSQL and Redis services
4. Configure environment variables properly
5. Deploy the frontend after the backend is working

Please help me implement this plan, starting with setting up a fresh backend service.
```

## Reference Files

Key files for deployment:

1. **docker-entrypoint.sh**
   - Located at: `/Users/vishalbharti/Downloads/rna-lab-deploy/backend/docker-entrypoint.sh`
   - Handles PostgreSQL connection check, migrations, and application startup

2. **railway.json**
   - Located at: `/Users/vishalbharti/Downloads/rna-lab-deploy/backend/railway.json`
   - Configures the Railway build and deployment process

3. **Dockerfile**
   - Located at: `/Users/vishalbharti/Downloads/rna-lab-deploy/backend/Dockerfile`
   - Currently causing issues with Railway detection

4. **Documentation**
   - DEPLOYMENT_GUIDE.md in the deployment repository
   - DEPLOYMENT_REFERENCE.md in the original repository

---

For more detailed information, refer to the comprehensive guides in both repositories.