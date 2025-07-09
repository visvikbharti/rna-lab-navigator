# 🚀 RNA Lab Navigator - Fresh Start Deployment Plan
**Date**: July 9, 2025  
**Target**: Lab NAS with Static IP
**Result**: Full-featured, self-hosted solution with zero platform limitations

## Why Lab NAS is Perfect

✅ **No platform limitations** - Install anything  
✅ **No credit card issues** - You own it  
✅ **Full ML models** - Enough RAM for everything  
✅ **Institute network** - Accessible to all lab members  
✅ **Your control** - Update anytime  
✅ **Professional setup** - Like enterprise deployment  

## Phase 1: Clean House (30 min)

### 1.1 Create Fresh Main Branch
```bash
# Save current work
git checkout pythonanywhere-deploy
git checkout -b backup-all-work-july-9

# Create clean main
git checkout main
git pull origin main
git checkout -b fresh-main-deploy

# Cherry-pick only good commits
git cherry-pick [commits with actual features]
```

### 1.2 Archive Old Branches
```bash
# List all branches
git branch -a

# Archive old attempts
git tag archive/railway-attempt origin/railway-deploy
git tag archive/pythonanywhere-attempt origin/pythonanywhere-deploy
git push --tags

# Delete old branches
git push origin --delete railway-deploy pythonanywhere-deploy fix-openai-api-v1
```

### 1.3 Create Clean Structure
```
rna-lab-navigator/
├── docker-compose.yml        # One file to rule them all
├── .env.example             # Clear documentation
├── deploy.sh                # One-command deployment
├── update.sh                # One-command updates
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt     # Single, working requirements
│   └── ...
├── frontend/
│   ├── Dockerfile
│   └── ...
└── nginx/
    └── nginx.conf           # Reverse proxy config
```

## Phase 2: Docker Compose Everything (45 min)

### 2.1 Complete docker-compose.yml
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: rna_lab_db
      POSTGRES_USER: rna_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rna_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Weaviate Vector DB
  weaviate:
    image: semitechnologies/weaviate:1.26.1
    restart: always
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 20
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-openai'
      ENABLE_MODULES: 'text2vec-openai'
      CLUSTER_HOSTNAME: 'node1'
      OPENAI_APIKEY: ${OPENAI_API_KEY}
    volumes:
      - weaviate_data:/var/lib/weaviate

  # Django Backend
  backend:
    build: ./backend
    restart: always
    depends_on:
      - postgres
      - redis
      - weaviate
    environment:
      - DATABASE_URL=postgresql://rna_user:${DB_PASSWORD}@postgres:5432/rna_lab_db
      - REDIS_URL=redis://redis:6379/0
      - WEAVIATE_URL=http://weaviate:8080
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=False
      - ALLOWED_HOSTS=*
    volumes:
      - ./backend:/app
      - static_volume:/app/static
      - media_volume:/app/media
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn rna_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4"

  # Celery Worker
  celery:
    build: ./backend
    restart: always
    depends_on:
      - backend
      - redis
    environment:
      - DATABASE_URL=postgresql://rna_user:${DB_PASSWORD}@postgres:5432/rna_lab_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    command: celery -A rna_backend worker -l info

  # Celery Beat
  celery-beat:
    build: ./backend
    restart: always
    depends_on:
      - backend
      - redis
    environment:
      - DATABASE_URL=postgresql://rna_user:${DB_PASSWORD}@postgres:5432/rna_lab_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    command: celery -A rna_backend beat -l info

  # React Frontend
  frontend:
    build: ./frontend
    restart: always
    environment:
      - VITE_API_URL=http://${LAB_STATIC_IP}/api
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run build

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/static
      - media_volume:/media
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  weaviate_data:
  static_volume:
  media_volume:
```

### 2.2 Nginx Configuration
```nginx
server {
    listen 80;
    server_name YOUR_LAB_STATIC_IP;
    client_max_body_size 100M;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /static/;
    }

    # Media files
    location /media/ {
        alias /media/;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2.3 Environment File
```bash
# .env
DB_PASSWORD=strong_password_here
SECRET_KEY=generate_with_django
OPENAI_API_KEY=sk-proj-your-key
LAB_STATIC_IP=your.lab.ip.here
```

## Phase 3: Deployment Scripts (15 min)

### 3.1 deploy.sh
```bash
#!/bin/bash
set -e

echo "🚀 RNA Lab Navigator Deployment"
echo "==============================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose required"; exit 1; }

# Load environment
if [ ! -f .env ]; then
    echo "Creating .env from .env.example"
    cp .env.example .env
    echo "Please edit .env with your values"
    exit 1
fi

# Pull latest code
echo "📦 Pulling latest code..."
git pull origin main

# Build and start
echo "🔨 Building containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 30

# Create superuser
echo "👤 Creating admin user..."
docker-compose exec backend python manage.py createsuperuser --noinput \
    --username admin --email admin@rnalab.com || true

# Load sample data
echo "📊 Loading sample data..."
docker-compose exec backend python manage.py loaddata fixtures/sample_data.json || true

# Show status
echo "✅ Deployment complete!"
echo ""
echo "📍 Access your app at: http://${LAB_STATIC_IP}"
echo "📍 Admin panel: http://${LAB_STATIC_IP}/admin"
echo "📍 API docs: http://${LAB_STATIC_IP}/api/docs"
echo ""
docker-compose ps
```

### 3.2 update.sh
```bash
#!/bin/bash
# For beta testing updates
set -e

echo "🔄 Updating RNA Lab Navigator..."
git pull origin main
docker-compose build backend frontend
docker-compose up -d
echo "✅ Update complete!"
```

## Phase 4: NAS Setup (30 min)

### 4.1 On Your NAS
```bash
# Install Docker and Docker Compose
# (Varies by NAS - Synology, QNAP, etc have package managers)

# Create project directory
mkdir -p /volume1/docker/rna-lab-navigator
cd /volume1/docker/rna-lab-navigator

# Clone your clean repo
git clone https://github.com/yourusername/rna-lab-navigator.git .

# Run deployment
./deploy.sh
```

### 4.2 Network Configuration
1. **Port Forwarding** (if needed):
   - 80 → NAS_IP:80
   - 443 → NAS_IP:443

2. **Firewall Rules**:
   - Allow institute network access
   - Block external access (security)

## Phase 5: Beta Testing Workflow

### For You (Developer)
```bash
# Make changes locally
git add .
git commit -m "Feature: Added XYZ"
git push origin main

# On NAS (via SSH)
ssh your-nas
cd /path/to/rna-lab-navigator
./update.sh
```

### For Beta Testers
- URL: `http://YOUR_LAB_STATIC_IP`
- Credentials: Provided separately
- Feedback: Built-in feedback form

## Success Metrics

✅ All ML models running locally  
✅ <5 second response times  
✅ No external dependencies  
✅ One-command updates  
✅ Full control  

## Troubleshooting

### If NAS doesn't support Docker:
**Option A**: Install Ubuntu Server on a spare lab computer  
**Option B**: Use Proxmox/VMware on NAS to run Ubuntu VM  
**Option C**: Get a small server (Intel NUC) for ~$500  

### If institute blocks ports:
- Use VPN server on NAS
- Use Tailscale for zero-config VPN
- Use CloudFlare Tunnel (free)

---

## 🎯 Action Items

1. **Today**: Clean up GitHub branches
2. **Tomorrow**: Set up Docker on NAS
3. **Day 3**: Deploy and test
4. **Day 4**: Share with beta testers

**This is how professionals deploy internal tools. No more platform nightmares!**