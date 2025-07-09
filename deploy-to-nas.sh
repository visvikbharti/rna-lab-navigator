#!/bin/bash
# RNA Lab Navigator - NAS Deployment Script
set -e

echo "🧬 RNA Lab Navigator - NAS Deployment"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env << EOF
# Database
DB_PASSWORD=$(openssl rand -base64 32)

# Django
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# OpenAI
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE

# Your Lab's Static IP
LAB_STATIC_IP=YOUR.LAB.IP.HERE

# Admin credentials
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@rnalab.com
DJANGO_SUPERUSER_PASSWORD=ChangeMeNow123!
EOF
    echo -e "${RED}⚠️  Please edit .env file with your actual values!${NC}"
    echo "Especially: OPENAI_API_KEY and LAB_STATIC_IP"
    exit 1
fi

# Load environment
source .env

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker first"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose first"
    exit 1
fi

# Stop any existing containers
echo -e "${BLUE}Stopping existing containers...${NC}"
docker-compose -f docker-compose.production.yml down 2>/dev/null || true

# Build images
echo -e "${BLUE}Building Docker images...${NC}"
docker-compose -f docker-compose.production.yml build

# Start services
echo -e "${BLUE}Starting all services...${NC}"
docker-compose -f docker-compose.production.yml up -d

# Wait for database
echo -e "${BLUE}Waiting for database to be ready...${NC}"
sleep 15

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
docker-compose -f docker-compose.production.yml exec -T backend python manage.py migrate

# Create superuser
echo -e "${BLUE}Creating admin user...${NC}"
docker-compose -f docker-compose.production.yml exec -T backend python manage.py createsuperuser --noinput || true

# Collect static files
echo -e "${BLUE}Collecting static files...${NC}"
docker-compose -f docker-compose.production.yml exec -T backend python manage.py collectstatic --noinput

# Load sample data (if exists)
if [ -f backend/fixtures/sample_data.json ]; then
    echo -e "${BLUE}Loading sample data...${NC}"
    docker-compose -f docker-compose.production.yml exec -T backend python manage.py loaddata fixtures/sample_data.json || true
fi

# Show running services
echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
docker-compose -f docker-compose.production.yml ps
echo ""
echo -e "${GREEN}🌐 Access your application at:${NC}"
echo -e "   ${BLUE}http://${LAB_STATIC_IP}${NC}"
echo ""
echo -e "${GREEN}👤 Admin Panel:${NC}"
echo -e "   ${BLUE}http://${LAB_STATIC_IP}/admin${NC}"
echo -e "   Username: ${DJANGO_SUPERUSER_USERNAME}"
echo -e "   Password: ${DJANGO_SUPERUSER_PASSWORD}"
echo ""
echo -e "${GREEN}📊 Service URLs:${NC}"
echo -e "   API: ${BLUE}http://${LAB_STATIC_IP}/api${NC}"
echo -e "   Weaviate: ${BLUE}http://${LAB_STATIC_IP}:8080${NC}"
echo ""
echo -e "${GREEN}📝 Logs:${NC}"
echo -e "   docker-compose -f docker-compose.production.yml logs -f backend"
echo ""