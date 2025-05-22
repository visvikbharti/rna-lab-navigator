# Deployment Guide

This guide provides comprehensive instructions for deploying the RNA Lab Navigator in various environments, from development to production.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Development Deployment](#development-deployment)
5. [Production Deployment](#production-deployment)
6. [Railway + Vercel Deployment](#railway--vercel-deployment)
7. [Self-Hosted Deployment](#self-hosted-deployment)
8. [Air-Gapped Deployment](#air-gapped-deployment)
9. [Backup and Recovery](#backup-and-recovery)
10. [Monitoring and Logging](#monitoring-and-logging)
11. [Scaling Guidelines](#scaling-guidelines)
12. [Troubleshooting](#troubleshooting)

## Deployment Options

RNA Lab Navigator supports several deployment options:

| Option | Description | Best For |
|--------|-------------|----------|
| Development | Local environment for development and testing | Developers, testing |
| Railway + Vercel | Cloud deployment using Railway and Vercel | Standard production use |
| Self-Hosted | Deployment to your own servers | Custom infrastructure |
| Air-Gapped | Fully isolated deployment without internet access | High security environments |

## Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| CPU | 2 cores | 4 cores | 8+ cores |
| RAM | 4 GB | 8 GB | 16+ GB |
| Storage | 20 GB | 50 GB | 100+ GB |
| Network | 10 Mbps | 100 Mbps | 1 Gbps |

### Software Requirements

- Docker and Docker Compose (v2.x+)
- Git
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Nginx (for production)

### External Services

- OpenAI API account (or alternative LLM provider)
- S3-compatible object storage (optional, for backups)
- SMTP server (for email notifications)

## Environment Configuration

### Environment Variables

Create and configure `.env` files with appropriate values:

#### Root `.env`

```env
# Docker Compose Configuration
COMPOSE_PROJECT_NAME=rna_lab_navigator
POSTGRES_PASSWORD=secure_password
POSTGRES_USER=rna_user
POSTGRES_DB=rna_db
REDIS_PASSWORD=secure_redis_password
```

#### Backend `.env`

```env
# Django Settings
DEBUG=False
SECRET_KEY=your_secure_secret_key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
TIME_ZONE=Asia/Kolkata

# Database Connection
DB_HOST=postgres
DB_PORT=5432
DB_NAME=rna_db
DB_USER=rna_user
DB_PASSWORD=secure_password

# Redis Connection
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure_redis_password

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_ORG_ID=your_openai_org_id
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Weaviate Configuration
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_MTLS_ENABLED=false
WEAVIATE_CERT_PATH=/app/certs/client.pem
WEAVIATE_KEY_PATH=/app/certs/client.key
WEAVIATE_CA_PATH=/app/certs/ca.pem

# LLM Network Isolation
LLM_ISOLATION_LEVEL=none  # none, proxy, air-gapped
OLLAMA_URL=http://ollama:11434  # For air-gapped mode

# Security Settings
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=true

# Backup Configuration
BACKUP_STORAGE=s3  # local or s3
S3_BUCKET_NAME=your-backup-bucket
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_ENDPOINT_URL=https://s3.amazonaws.com
BACKUP_RETENTION_DAYS=30

# Email Configuration
EMAIL_HOST=smtp.your-domain.com
EMAIL_PORT=587
EMAIL_HOST_USER=alerts@your-domain.com
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=RNA Lab Navigator <no-reply@your-domain.com>
```

## Development Deployment

Follow these steps for a local development environment:

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/rna-lab-navigator.git
cd rna-lab-navigator
```

### Step 2: Environment Setup

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Edit the `.env` files with your configuration.

### Step 3: Start Docker Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache and message broker
- Weaviate vector database

### Step 4: Set Up Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Step 5: Start Celery Workers

In separate terminal windows:

```bash
# Terminal 1
cd backend
source venv/bin/activate
celery -A rna_backend worker -l info

# Terminal 2
cd backend
source venv/bin/activate
celery -A rna_backend beat -l info
```

### Step 6: Set Up Frontend

```bash
cd frontend
npm install
npm run dev
```

### Step 7: Load Sample Data

```bash
cd backend
python api/ingestion/ingest_thesis.py ../data/sample_docs/theses/2025_Phutela_Rhythm_PhD_Thesis.pdf "Rhythm Phutela" 2025
```

## Production Deployment

### Railway + Vercel Deployment

The recommended approach for production deployment is using Railway for the backend and Vercel for the frontend.

#### Step 1: Prepare for Railway Deployment

1. Create a Railway account and install the CLI:

```bash
npm install -g @railway/cli
railway login
```

2. Initialize the Railway project:

```bash
railway init
```

3. Add your environment variables in the Railway dashboard.

#### Step 2: Deploy Backend to Railway

```bash
cd backend
railway up
```

This will:
- Build and deploy the Django application
- Set up PostgreSQL, Redis, and Weaviate
- Configure Celery workers
- Run migrations automatically

#### Step 3: Prepare for Vercel Deployment

1. Create a Vercel account and install the CLI:

```bash
npm install -g vercel
vercel login
```

2. Update the API endpoint in `frontend/src/api/query.js` to point to your Railway deployment.

#### Step 4: Deploy Frontend to Vercel

```bash
cd frontend
vercel --prod
```

This will:
- Build and optimize the React application
- Deploy to Vercel's global CDN
- Configure custom domain if specified

#### Step 5: Link Railway and Vercel

Configure your custom domain in both Railway and Vercel dashboards to ensure proper routing.

## Self-Hosted Deployment

For deploying to your own infrastructure:

### Step 1: Prepare Server

1. Install Docker and Docker Compose:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

2. Install Nginx:

```bash
sudo apt install -y nginx
```

### Step 2: Clone Repository

```bash
git clone https://github.com/your-org/rna-lab-navigator.git
cd rna-lab-navigator
```

### Step 3: Configure Environment

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Edit the `.env` files with production values.

### Step 4: Build and Deploy with Docker Compose

```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Step 5: Configure Nginx

Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/rna-lab-navigator
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://api.openai.com; font-src 'self';" always;
    
    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
    
    # Static files
    location /static/ {
        alias /var/www/rna-lab-navigator/static/;
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/rna-lab-navigator/media/;
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
    
    # Frontend
    location / {
        root /var/www/rna-lab-navigator/frontend;
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, max-age=3600";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/rna-lab-navigator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: Set Up SSL with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Step 7: Build and Deploy Frontend

```bash
cd frontend
npm install
npm run build
sudo mkdir -p /var/www/rna-lab-navigator/frontend
sudo cp -r dist/* /var/www/rna-lab-navigator/frontend/
```

### Step 8: Collect Static Files

```bash
cd backend
docker-compose -f ../docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
sudo mkdir -p /var/www/rna-lab-navigator/static
sudo cp -r staticfiles/* /var/www/rna-lab-navigator/static/
```

## Air-Gapped Deployment

For environments without internet access:

### Step 1: Prepare Installation Package

On an internet-connected machine:

```bash
# Clone repository
git clone https://github.com/your-org/rna-lab-navigator.git
cd rna-lab-navigator

# Download Docker images
docker-compose pull
docker save -o rna-images.tar $(docker-compose config --services | xargs -I{} docker-compose images {} -q)

# Download Python dependencies
pip download -r backend/requirements.txt -d backend/packages/

# Download Node.js dependencies
cd frontend
npm ci
cd ..
tar -czf frontend-node-modules.tar.gz frontend/node_modules/

# Download LLM models for Ollama
docker run --rm -v $(pwd)/models:/models ollama/ollama pull llama2:7b
docker run --rm -v $(pwd)/models:/models ollama/ollama pull mistral:7b
docker run --rm -v $(pwd)/models:/models ollama/ollama pull orca2:7b

# Create installation package
tar -czf rna-lab-navigator-installation.tar.gz \
    rna-images.tar backend/packages/ \
    frontend-node-modules.tar.gz models/ \
    docker-compose.yml docker-compose.air-gapped.yml \
    .env.example backend/.env.example
```

### Step 2: Transfer and Install

Transfer the installation package to the air-gapped environment and:

```bash
# Extract package
tar -xzf rna-lab-navigator-installation.tar.gz

# Load Docker images
docker load -i rna-images.tar

# Set up environment
cp .env.example .env
cp backend/.env.example backend/.env
```

Edit `.env` files with air-gapped configuration:

```env
# In backend/.env
LLM_ISOLATION_LEVEL=air-gapped
OLLAMA_URL=http://ollama:11434
```

### Step 3: Install Python Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install --no-index --find-links=packages/ -r requirements.txt
```

### Step 4: Install Node.js Dependencies

```bash
cd frontend
tar -xzf ../frontend-node-modules.tar.gz
```

### Step 5: Launch Services

```bash
docker-compose -f docker-compose.air-gapped.yml up -d
```

This special Docker Compose file includes Ollama with pre-downloaded models.

### Step 6: Initialize Database and Load Models

```bash
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py load_local_models
```

## Backup and Recovery

### Configuring Automated Backups

Backups are automatically configured when you set the appropriate environment variables:

```env
# In backend/.env
BACKUP_STORAGE=s3  # or local
BACKUP_RETENTION_DAYS=30
```

For S3 storage:
```env
S3_BUCKET_NAME=your-backup-bucket
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_ENDPOINT_URL=https://s3.amazonaws.com
```

Backups include:
- PostgreSQL database
- Weaviate data
- Uploaded media files
- Configuration files

### Manual Backup

To trigger a manual backup:

```bash
cd backend
python manage.py backup --full
```

### System Recovery

To restore from a backup:

1. Identify the backup ID:

```bash
python manage.py list_backups
```

2. Restore the system:

```bash
python manage.py restore --backup-id=20250601-120000
```

For disaster recovery, follow these steps:

1. Install a fresh system following the deployment guide
2. Set up the same environment variables
3. Run the restore command
4. Verify system functionality

## Monitoring and Logging

### Setting Up Monitoring

The RNA Lab Navigator includes a monitoring stack with:
- Prometheus for metrics collection
- Grafana for dashboards
- Loki for log aggregation

Deploy the monitoring stack:

```bash
cd monitoring
docker-compose up -d
```

Access Grafana at http://your-server:3000 (default credentials: admin/admin)

### Important Metrics to Monitor

| Metric | Description | Warning Threshold | Critical Threshold |
|--------|-------------|-------------------|-------------------|
| api_request_time | API response time | > 1000ms | > 3000ms |
| llm_generation_time | LLM generation time | > 3000ms | > 10000ms |
| query_confidence | Answer confidence score | < 0.6 | < 0.45 |
| database_connections | Active DB connections | > 80% pool | > 95% pool |
| cpu_usage | Server CPU usage | > 70% | > 90% |
| memory_usage | Server memory usage | > 80% | > 90% |
| disk_usage | Server disk usage | > 80% | > 90% |

### Log Aggregation

Logs are collected centrally and can be viewed in Grafana:
- Application logs from Django
- Access logs from Nginx
- Container logs from Docker
- System logs from the host

## Scaling Guidelines

### Vertical Scaling

For smaller deployments, increasing resources on a single server:
- Increase CPU and memory for the server
- Allocate more resources to Weaviate and PostgreSQL
- Adjust cache sizes in Redis

### Horizontal Scaling

For larger deployments, distribute across multiple servers:
- Deploy Django application across multiple servers with load balancing
- Set up PostgreSQL replication
- Configure Redis cluster
- Implement Weaviate cluster

### Service-Specific Scaling

Guidelines for scaling individual services:

| Service | Scaling Method | Notes |
|---------|----------------|-------|
| Django | Add more application servers | Stateless, easy to scale |
| Celery | Add more worker processes | Group by task type |
| PostgreSQL | Primary/replica setup | Consider managed services |
| Redis | Redis Cluster | For high availability |
| Weaviate | Weaviate cluster | Scale with data volume |
| Nginx | Load balancer with multiple instances | For high traffic |

## Troubleshooting

### Common Issues and Solutions

#### Backend Not Starting

**Symptoms**: Django service fails to start, errors in logs

**Possible causes and solutions**:
- Database connection issues: Check PostgreSQL is running, credentials are correct
- Migration errors: Run `python manage.py migrate` manually
- Port conflicts: Check if port 8000 is available
- Environment variables: Verify all required variables are set

#### Celery Workers Not Processing Tasks

**Symptoms**: Tasks stay in "pending" state, no worker logs

**Possible causes and solutions**:
- Redis connection issues: Verify Redis is running
- Worker not started: Check Celery worker process
- Task routing issues: Check task queue configuration
- Resource limitations: Check CPU and memory usage

#### Vector Search Not Working

**Symptoms**: Searches return no results or irrelevant results

**Possible causes and solutions**:
- Weaviate not running: Check container status
- No data ingested: Verify documents were properly ingested
- Incorrect embeddings: Check OpenAI API key and embedding model
- Index issues: Try rebuilding the index

#### High Latency

**Symptoms**: Slow response times, timeouts

**Possible causes and solutions**:
- Insufficient resources: Check CPU, memory, and disk I/O
- Network issues: Check latency to OpenAI API
- Database performance: Check query performance
- Caching issues: Verify Redis is working correctly

### Diagnostics and Logs

Key logs to check when troubleshooting:

- Django logs: `/var/log/app/django.log`
- Celery logs: `/var/log/app/celery.log`
- Nginx access logs: `/var/log/nginx/access.log`
- Nginx error logs: `/var/log/nginx/error.log`
- Docker logs: `docker logs container_name`

System diagnosis commands:

```bash
# Check system status
docker-compose ps
docker stats

# Check Django logs
docker-compose logs backend

# Check Celery logs
docker-compose logs celery_worker
docker-compose logs celery_beat

# Check database status
docker-compose exec postgres pg_isready

# Check Redis status
docker-compose exec redis redis-cli ping

# Check Weaviate status
curl http://localhost:8080/v1/meta
```

### Getting Help

If you encounter issues not covered in this guide:

1. Check the [Troubleshooting Guide](docs/user_guide/troubleshooting.md) for detailed solutions
2. Review logs for specific error messages
3. Check for known issues in the project's issue tracker
4. Contact the lab administrator or development team for assistance