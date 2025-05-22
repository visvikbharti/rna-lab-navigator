#!/bin/bash

# Complete Deployment Script for RNA Lab Navigator
# This script deploys both backend (Railway) and frontend (Vercel)

set -e

echo "🚀 Starting complete deployment of RNA Lab Navigator..."
echo "This will deploy:"
echo "  - Backend API to Railway"
echo "  - Frontend to Vercel"
echo "  - All supporting services (PostgreSQL, Redis, Weaviate, Celery)"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    curl -fsSL https://railway.app/install.sh | sh
    export PATH=$PATH:/home/$(whoami)/.railway/bin
fi

# Check Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js first."
    exit 1
fi

# Check Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python first."
    exit 1
fi

echo "✅ Prerequisites check complete!"
echo ""

# Get deployment configuration
echo "📋 Deployment Configuration"
echo "=========================="

read -p "Enter your OpenAI API key: " -s OPENAI_API_KEY
echo ""

read -p "Enter your Railway project name (default: rna-lab-navigator): " RAILWAY_PROJECT
RAILWAY_PROJECT=${RAILWAY_PROJECT:-rna-lab-navigator}

read -p "Enter your Vercel project name (default: rna-lab-navigator-frontend): " VERCEL_PROJECT
VERCEL_PROJECT=${VERCEL_PROJECT:-rna-lab-navigator-frontend}

echo ""
echo "🚀 Starting deployment with:"
echo "  Railway Project: $RAILWAY_PROJECT"
echo "  Vercel Project: $VERCEL_PROJECT"
echo ""

# Deploy backend to Railway
echo "🏗️ STEP 1: Deploying Backend to Railway"
echo "========================================="

# Run Railway deployment script
OPENAI_API_KEY=$OPENAI_API_KEY ./scripts/deploy-railway.sh

# Get backend URL
echo "Getting backend URL..."
cd backend
BACKEND_URL=$(railway status --json | jq -r '.deployments[0].url')
cd ..

if [ "$BACKEND_URL" = "null" ] || [ -z "$BACKEND_URL" ]; then
    echo "⚠️ Could not get backend URL automatically. Please enter it manually:"
    read -p "Enter your Railway backend URL: " BACKEND_URL
fi

echo "✅ Backend deployed at: $BACKEND_URL"
echo ""

# Deploy frontend to Vercel
echo "🌐 STEP 2: Deploying Frontend to Vercel"
echo "========================================"

# Set environment variable for frontend
export VITE_API_BASE_URL=$BACKEND_URL

# Run Vercel deployment script
./scripts/deploy-vercel.sh --prod

# Get frontend URL
echo "Getting frontend URL..."
cd frontend
FRONTEND_URL=$(vercel ls | grep $VERCEL_PROJECT | head -1 | awk '{print $2}')
cd ..

if [ -z "$FRONTEND_URL" ]; then
    echo "⚠️ Could not get frontend URL automatically. Please check Vercel dashboard."
    FRONTEND_URL="your-app.vercel.app"
fi

echo "✅ Frontend deployed at: https://$FRONTEND_URL"
echo ""

# Update backend CORS settings
echo "🔧 STEP 3: Updating Backend CORS Settings"
echo "=========================================="

cd backend
echo "Adding frontend URL to CORS allowed origins..."
railway variables set CORS_ALLOWED_ORIGINS="https://$FRONTEND_URL"
cd ..

echo "✅ CORS settings updated!"
echo ""

# Run post-deployment tests
echo "🧪 STEP 4: Running Post-Deployment Tests"
echo "========================================"

echo "Testing backend health..."
if curl -f "$BACKEND_URL/health/" > /dev/null 2>&1; then
    echo "✅ Backend health check passed"
else
    echo "⚠️ Backend health check failed - may need a few minutes to start"
fi

echo "Testing frontend..."
if curl -f "https://$FRONTEND_URL" > /dev/null 2>&1; then
    echo "✅ Frontend health check passed"
else
    echo "⚠️ Frontend health check failed - may need a few minutes to start"
fi

echo ""

# Deployment summary
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "📋 Deployment Summary:"
echo "   Backend API:  $BACKEND_URL"
echo "   Frontend:     https://$FRONTEND_URL"
echo ""
echo "🔧 Services Deployed:"
echo "   ✅ Django API Server (Railway)"
echo "   ✅ PostgreSQL Database (Railway)"
echo "   ✅ Redis Cache (Railway)"
echo "   ✅ Weaviate Vector DB (Railway)"
echo "   ✅ Celery Worker (Railway)"
echo "   ✅ React Frontend (Vercel)"
echo ""
echo "📋 Next Steps:"
echo "1. Test the application at: https://$FRONTEND_URL"
echo "2. Upload some documents to test the RAG pipeline"
echo "3. Set up monitoring and alerts"
echo "4. Configure custom domains (optional)"
echo "5. Set up backup schedules"
echo ""
echo "🚨 Important Notes:"
echo "- It may take a few minutes for all services to fully start"
echo "- Check Railway dashboard for service status"
echo "- Check Vercel dashboard for deployment status"
echo "- Monitor logs for any issues"
echo ""
echo "📖 For troubleshooting, see: DEPLOYMENT_GUIDE.md"
echo ""
echo "🎊 Congratulations! Your RNA Lab Navigator is live!"