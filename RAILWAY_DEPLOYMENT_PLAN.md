# Railway Deployment Plan - Full ML Features
**Time Required: 45-60 minutes**
**Result: Your exact localhost demo running in production**

## 🎯 Why Railway Instead of PythonAnywhere

### What You Demonstrated (Localhost):
- ✅ Sentence Transformers embeddings
- ✅ Cross-encoder reranking  
- ✅ Weaviate vector search
- ✅ Redis caching (<5s responses)
- ✅ Async document processing

### What PythonAnywhere Gives:
- ❌ Basic keyword search only
- ❌ No ML models (512MB RAM limit)
- ❌ No vector search
- ❌ No caching
- ❌ Slow responses

## 📋 Step-by-Step Railway Deployment

### Step 1: Create Railway Account (5 min)
1. Go to https://railway.app
2. Sign up with GitHub (recommended)
3. You'll get $5 free credits (enough for beta testing)

### Step 2: Install Railway CLI (3 min)
```bash
# macOS
brew install railway

# Or via npm
npm install -g @railway/cli

# Login
railway login
```

### Step 3: Create New Railway Project (2 min)
```bash
cd /Users/vishalbharti/Downloads/rna-lab-navigator
railway init
# Choose "Empty Project"
# Name it: rna-lab-navigator
```

### Step 4: Deploy Services (15 min)

#### A. PostgreSQL
```bash
railway add
# Select "PostgreSQL"
# This creates a managed PostgreSQL instance
```

#### B. Redis
```bash
railway add
# Select "Redis"
# This creates a managed Redis instance
```

#### C. Add Weaviate Service
Create a new file `railway.services.yml`:
```yaml
services:
  weaviate:
    image: semitechnologies/weaviate:1.26.1
    variables:
      QUERY_DEFAULTS_LIMIT: 20
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: true
      DEFAULT_VECTORIZER_MODULE: text2vec-openai
      ENABLE_MODULES: text2vec-openai
      CLUSTER_HOSTNAME: node1
    healthcheck:
      path: /v1/.well-known/ready
      interval: 10
```

```bash
railway up -s weaviate
```

### Step 5: Set Environment Variables (10 min)
```bash
# Set all required environment variables
railway variables set DJANGO_SETTINGS_MODULE=rna_backend.settings
railway variables set SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
railway variables set OPENAI_API_KEY="sk-proj-YOUR_ACTUAL_KEY_HERE"
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS="*.railway.app,localhost"
railway variables set CORS_ALLOWED_ORIGINS="https://rna-lab-navigator.vercel.app"

# Database will be auto-configured by Railway
# Redis URL will be auto-configured by Railway
```

### Step 6: Deploy Backend with Full ML Features (10 min)

First, ensure your backend uses the FULL settings (not pythonanywhere):

```bash
cd backend

# Create a Railway-specific Procfile
cat > Procfile << 'EOF'
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn rna_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
worker: celery -A rna_backend worker -l info
beat: celery -A rna_backend beat -l info
EOF

# Deploy
railway up
```

### Step 7: Get Backend URL (1 min)
```bash
railway domain
# This will give you something like: rna-lab-navigator-production.up.railway.app
```

### Step 8: Update Frontend Environment (5 min)
1. Go to Vercel Dashboard
2. Navigate to your project settings
3. Update environment variable:
   ```
   VITE_API_URL=https://rna-lab-navigator-production.up.railway.app
   ```
4. Redeploy frontend

### Step 9: Initialize Database & Create Admin (5 min)
```bash
# Connect to Railway shell
railway run python manage.py createsuperuser
# Username: admin
# Email: admin@rnalab.com  
# Password: GODisone@1

# Load sample data
railway run python manage.py loaddata fixtures/sample_data.json
```

### Step 10: Test Full Functionality (5 min)
1. Open frontend URL
2. Login with admin credentials
3. Test:
   - Document upload
   - Vector search query
   - Check response time (<5s)
   - Verify citations and sources

## 🎯 Expected Results

### Performance Metrics:
- **Query Response Time**: <5 seconds ✅
- **Answer Quality**: Same as localhost demo ✅
- **Document Processing**: Async with progress ✅
- **Search Type**: Hybrid (BM25 + Vector) ✅

### Cost Estimate:
- **Development/Beta**: Free tier ($5 credit)
- **Production**: ~$20-30/month for full stack
- **Alternative**: Can optimize to ~$10-15/month

## 🆘 Troubleshooting

### If deployment fails:
```bash
# Check logs
railway logs

# Check service status
railway status

# Restart services
railway restart
```

### If ML models don't load:
```bash
# Increase memory allocation
railway variables set WEB_MEMORY=2048
railway restart
```

## 📝 Alternative: Quick Digital Ocean Deploy

If Railway doesn't work, we can deploy on DigitalOcean in 30 minutes:
1. $200 free credit for 60 days
2. One-click Docker deployment
3. Full control over resources

## ✅ Success Criteria
- [ ] Login works without errors
- [ ] Vector search returns relevant results
- [ ] Response time <5 seconds
- [ ] All features from localhost demo work
- [ ] Beta testers can access without issues

---

**Ready to start? Let's begin with Step 1 - Creating your Railway account.**