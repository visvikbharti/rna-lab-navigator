# 🚀 NAS Deployment - Quick Start Guide

## What You Get
✅ **Full ML capabilities** - All models running locally  
✅ **Your control** - No platform limitations  
✅ **Professional setup** - Docker-based like enterprises  
✅ **Easy updates** - One command to update during beta  

## Prerequisites on Your NAS
- Docker installed
- Docker Compose installed
- At least 8GB RAM available
- Your static IP configured

## Step 1: Prepare Your NAS (10 min)

SSH into your NAS:
```bash
ssh your-username@your-nas-ip
```

Create project directory:
```bash
mkdir -p /volume1/docker/rna-lab  # Adjust path for your NAS
cd /volume1/docker/rna-lab
```

Clone your repository:
```bash
git clone https://github.com/visvikbharti/rna-lab-navigator.git .
```

## Step 2: Configure Environment (5 min)

Copy and edit the environment file:
```bash
cp .env.example .env
nano .env  # or vim .env
```

**MUST CHANGE**:
- `OPENAI_API_KEY` - Your actual OpenAI key
- `LAB_STATIC_IP` - Your lab's static IP
- `DJANGO_SUPERUSER_PASSWORD` - Admin password

## Step 3: Deploy! (20 min)

Run the deployment script:
```bash
./deploy-to-nas.sh
```

This will:
1. Build all Docker images
2. Start PostgreSQL, Redis, Weaviate
3. Start Django backend with Celery
4. Build React frontend
5. Configure Nginx reverse proxy
6. Create admin user
7. Run migrations

## Step 4: Access Your App

Once deployment completes:
- **App**: http://YOUR_LAB_IP
- **Admin**: http://YOUR_LAB_IP/admin
- **API**: http://YOUR_LAB_IP/api

## For Beta Testing Updates

When you make changes:
```bash
# On your local machine
git add .
git commit -m "Added new feature"
git push origin main

# On NAS
ssh your-nas
cd /volume1/docker/rna-lab
./update-app.sh
```

## Troubleshooting

### Check logs:
```bash
# All services
docker-compose -f docker-compose.production.yml logs

# Specific service
docker-compose -f docker-compose.production.yml logs backend
docker-compose -f docker-compose.production.yml logs nginx
```

### Restart services:
```bash
docker-compose -f docker-compose.production.yml restart backend
```

### Stop everything:
```bash
docker-compose -f docker-compose.production.yml down
```

### Remove everything and start fresh:
```bash
docker-compose -f docker-compose.production.yml down -v
./deploy-to-nas.sh
```

## Memory Usage

Expected RAM usage:
- PostgreSQL: ~500MB
- Redis: ~100MB
- Weaviate: ~1GB
- Django + ML models: ~2-3GB
- Nginx: ~50MB
- **Total**: ~4-5GB

## Security Notes

1. **Firewall**: Only allow institute IPs
2. **HTTPS**: Can add Let's Encrypt later
3. **Backups**: Set up automated backups on NAS

## Beta Testing Checklist

- [ ] Deploy on NAS
- [ ] Test login functionality
- [ ] Upload a test document
- [ ] Run a query - verify <5s response
- [ ] Check ML features work (semantic search)
- [ ] Share URL with 5 beta testers
- [ ] Set up feedback collection

---

**🎉 No more platform nightmares! You own this deployment!**