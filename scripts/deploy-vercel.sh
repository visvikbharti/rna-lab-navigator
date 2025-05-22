#!/bin/bash

# Vercel Deployment Script for RNA Lab Navigator Frontend
# This script deploys the frontend to Vercel

set -e

echo "🚀 Starting Vercel deployment for RNA Lab Navigator Frontend..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check if backend URL is set
if [ -z "$VITE_API_BASE_URL" ]; then
    echo "⚠️ VITE_API_BASE_URL not set."
    read -p "Enter your Railway backend URL (e.g., https://your-app.railway.app): " BACKEND_URL
    export VITE_API_BASE_URL=$BACKEND_URL
    echo "VITE_API_BASE_URL=$BACKEND_URL" >> .env.production
fi

# Build the application
echo "🔨 Building application..."
npm run build

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
if [ "$1" = "--prod" ]; then
    echo "🌟 Deploying to production..."
    vercel --prod --env VITE_API_BASE_URL="$VITE_API_BASE_URL"
else
    echo "🧪 Deploying to preview..."
    vercel --env VITE_API_BASE_URL="$VITE_API_BASE_URL"
fi

# Get deployment URL
FRONTEND_URL=$(vercel ls | grep rna-lab-navigator | head -1 | awk '{print $2}')

echo "✅ Vercel deployment complete!"
echo ""
echo "🎉 Your RNA Lab Navigator frontend is now deployed:"
echo "   Frontend URL: https://$FRONTEND_URL"
echo ""
echo "📋 Next steps:"
echo "1. Update your backend CORS_ALLOWED_ORIGINS to include: https://$FRONTEND_URL"
echo "2. Set up custom domain in Vercel dashboard"
echo "3. Configure environment variables in Vercel dashboard"
echo "4. Set up monitoring and analytics"
echo ""
echo "⚙️ Environment variables to set in Vercel:"
echo "   VITE_API_BASE_URL=$VITE_API_BASE_URL"
echo ""
echo "📖 For more information, see: docs/deployment_guide.md"