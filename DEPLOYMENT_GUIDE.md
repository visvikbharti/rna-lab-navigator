# Railway & Vercel Deployment Guide

This guide provides step-by-step instructions for deploying the RNA Lab Navigator to Railway (backend) and Vercel (frontend).

## 🎯 Quick Start

### Prerequisites
- Railway CLI installed (`curl -fsSL https://railway.app/install.sh | sh`)
- Vercel CLI installed (`npm install -g vercel`)
- OpenAI API key
- Git repository access

### One-Command Deployment
```bash
# Backend (Railway)
./scripts/deploy-railway.sh

# Frontend (Vercel)
./scripts/deploy-vercel.sh --prod
```

## 🏗️ Architecture Overview

The deployment consists of 5 Railway services and 1 Vercel app:

### Railway Services
1. **Main Backend** - Django API server
2. **PostgreSQL** - Primary database
3. **Redis** - Cache and Celery broker
4. **Weaviate** - Vector database
5. **Celery Worker** - Background task processing
6. **Celery Beat** - Task scheduling (optional)

### Vercel App
- **Frontend** - React application

## 🚀 Backend Deployment (Railway)

### Step 1: Setup Railway Project

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login
railway login

# Create project
railway create rna-lab-navigator-backend
```

### Step 2: Deploy Database Services

```bash
# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis

# Deploy Weaviate (custom)
railway create weaviate
cp weaviate.railway.json railway.json
railway up
```

### Step 3: Configure Environment Variables

Copy the template and fill in your values:
```bash
cp backend/railway.env.template backend/railway.env.local
```

Required variables:
```env
SECRET_KEY=your-super-secret-production-key
OPENAI_API_KEY=sk-your-openai-key
ALLOWED_HOSTS=your-app.railway.app
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

Set in Railway:
```bash
railway variables set --file backend/railway.env.local
```

### Step 4: Deploy Main Application

```bash
cd backend
railway up --detach
```

### Step 5: Deploy Celery Services

```bash
# Worker
railway create celery-worker
railway up --config celery-worker.railway.json --detach

# Beat (optional)
railway create celery-beat
railway up --config celery-beat.railway.json --detach
```

### Step 6: Initialize Database

```bash
railway run python manage.py migrate
railway run python manage.py collectstatic --noinput
railway run python scripts/load_sample_data.py
```

## 🌐 Frontend Deployment (Vercel)

### Step 1: Setup Vercel Project

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Initialize project
cd frontend
vercel
```

### Step 2: Configure Environment Variables

Set in Vercel dashboard or CLI:
```bash
vercel env add VITE_API_BASE_URL production https://your-backend.railway.app
```

### Step 3: Deploy

```bash
# Production deployment
vercel --prod
```

## ⚙️ Environment Variables

### Backend (Railway)

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key | ✅ | `your-secret-key` |
| `OPENAI_API_KEY` | OpenAI API key | ✅ | `sk-...` |
| `DATABASE_URL` | PostgreSQL URL | ✅ | Auto-provided by Railway |
| `REDIS_URL` | Redis URL | ✅ | Auto-provided by Railway |
| `WEAVIATE_URL` | Weaviate endpoint | ✅ | `https://weaviate.railway.app` |
| `ALLOWED_HOSTS` | Django allowed hosts | ✅ | `app.railway.app` |
| `CORS_ALLOWED_ORIGINS` | CORS origins | ✅ | `https://app.vercel.app` |
| `DEBUG` | Debug mode | ❌ | `False` |

### Frontend (Vercel)

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `VITE_API_BASE_URL` | Backend API URL | ✅ | `https://backend.railway.app` |
| `VITE_APP_NAME` | Application name | ❌ | `RNA Lab Navigator` |
| `VITE_ENVIRONMENT` | Environment | ❌ | `production` |

## 🔧 Configuration Files

### Railway Configuration Files

- `backend/railway.json` - Main backend service
- `weaviate.railway.json` - Weaviate vector database
- `backend/celery-worker.railway.json` - Celery worker
- `backend/celery-beat.railway.json` - Celery beat scheduler

### Vercel Configuration Files

- `frontend/vercel.json` - Vercel deployment config
- `frontend/.env.production` - Production environment variables

### Docker Files

- `backend/Dockerfile` - Main backend container
- `Dockerfile.weaviate` - Weaviate container
- `backend/Dockerfile.celery-worker` - Celery worker container
- `backend/Dockerfile.celery-beat` - Celery beat container

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check database URL
railway run echo $DATABASE_URL

# Test connection
railway run python manage.py dbshell
```

#### 2. Weaviate Connection Failed
```bash
# Check Weaviate status
curl https://your-weaviate.railway.app/v1/.well-known/ready

# Check environment variable
railway run echo $WEAVIATE_URL
```

#### 3. CORS Errors
Ensure `CORS_ALLOWED_ORIGINS` includes your frontend URL:
```bash
railway variables set CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

#### 4. Static Files Not Loading
```bash
# Collect static files
railway run python manage.py collectstatic --noinput
```

### Logs and Monitoring

```bash
# Backend logs
railway logs

# Specific service logs
railway logs --service celery-worker

# Real-time logs
railway logs --follow
```

## 🔒 Security Checklist

- [ ] SECRET_KEY is secure and unique
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] CORS_ALLOWED_ORIGINS restricted to your domains
- [ ] OpenAI API key is secure
- [ ] Database credentials are secure
- [ ] HTTPS enabled (automatic on Railway/Vercel)
- [ ] Security headers configured
- [ ] Rate limiting enabled

## 📊 Performance Optimization

### Railway Settings
- Use 2-3 Gunicorn workers
- Enable gzip compression
- Configure proper health checks
- Set up monitoring

### Vercel Settings
- Enable Edge Network
- Configure caching headers
- Optimize build process
- Use environment-specific builds

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Railway
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          curl -fsSL https://railway.app/install.sh | sh
          railway login --token ${{ secrets.RAILWAY_TOKEN }}
          railway up --detach
```

## 📋 Maintenance

### Regular Tasks
- Monitor application logs
- Check database performance
- Update dependencies
- Backup data
- Monitor costs

### Scaling
- Increase Railway service replicas
- Optimize database queries
- Use Vercel Edge Functions
- Implement caching strategies

## 🆘 Support

For deployment issues:
1. Check logs: `railway logs`
2. Verify environment variables
3. Test individual services
4. Review this documentation
5. Open GitHub issue

## 🎉 Success Checklist

After deployment, verify:
- [ ] Backend API responds: `https://your-backend.railway.app/health/`
- [ ] Frontend loads: `https://your-frontend.vercel.app`
- [ ] Search functionality works
- [ ] File upload works
- [ ] Database migrations applied
- [ ] Sample data loaded
- [ ] SSL certificates active
- [ ] Environment variables set

Congratulations! Your RNA Lab Navigator is now deployed and ready for use! 🚀