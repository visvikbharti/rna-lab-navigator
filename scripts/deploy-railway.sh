#!/bin/bash

# Railway Deployment Script for RNA Lab Navigator Backend
# This script deploys the complete stack to Railway

set -e

echo "🚀 Starting Railway deployment for RNA Lab Navigator Backend..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    curl -fsSL https://railway.app/install.sh | sh
    export PATH=$PATH:/home/$(whoami)/.railway/bin
fi

# Login to Railway (if not already logged in)
echo "🔐 Logging into Railway..."
railway login

# Create new Railway project if it doesn't exist
echo "📦 Setting up Railway project..."
if ! railway status &> /dev/null; then
    echo "Creating new Railway project..."
    railway create rna-lab-navigator-backend
fi

# Deploy PostgreSQL database
echo "🗄️ Deploying PostgreSQL database..."
railway add postgresql

# Deploy Redis
echo "🔴 Deploying Redis..."
railway add redis

# Deploy Weaviate vector database
echo "🧮 Deploying Weaviate..."
railway create weaviate --from-template=weaviate

# Set environment variables
echo "⚙️ Setting environment variables..."
if [ -f "backend/railway.env.local" ]; then
    echo "Loading environment variables from railway.env.local..."
    railway variables set --file backend/railway.env.local
else
    echo "⚠️ railway.env.local not found. Setting essential variables..."
    echo "Please set these variables manually in Railway dashboard:"
    echo "- SECRET_KEY"
    echo "- OPENAI_API_KEY"
    echo "- ALLOWED_HOSTS"
    echo "- CORS_ALLOWED_ORIGINS"
fi

# Deploy main backend application
echo "🚀 Deploying main backend application..."
cd backend
railway up --detach

# Deploy Celery worker
echo "👷 Deploying Celery worker..."
railway create celery-worker
railway link
railway up --config celery-worker.railway.json --detach

# Deploy Celery beat scheduler
echo "⏰ Deploying Celery beat scheduler..."
railway create celery-beat
railway link
railway up --config celery-beat.railway.json --detach

# Get deployment URLs
echo "📋 Getting deployment information..."
BACKEND_URL=$(railway status --json | jq -r '.deployments[0].url')
echo "✅ Backend deployed at: $BACKEND_URL"

# Run initial migrations and data loading
echo "🔧 Running initial setup..."
railway run python manage.py migrate
railway run python manage.py collectstatic --noinput
railway run python manage.py loaddata initial_data || echo "⚠️ No initial data fixture found"

# Load sample data if requested
read -p "🎯 Load sample documents for demo? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📚 Loading sample documents..."
    railway run python scripts/load_sample_data.py
fi

echo "✅ Railway deployment complete!"
echo ""
echo "🎉 Your RNA Lab Navigator backend is now deployed:"
echo "   Backend API: $BACKEND_URL"
echo ""
echo "📋 Next steps:"
echo "1. Configure your frontend to use: $BACKEND_URL"
echo "2. Set up custom domain in Railway dashboard"
echo "3. Configure SSL certificates"
echo "4. Set up monitoring and alerts"
echo ""
echo "📖 For more information, see: docs/deployment_guide.md"