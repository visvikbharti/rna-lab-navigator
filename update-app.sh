#!/bin/bash
# Quick update script for beta testing
set -e

echo "🔄 Updating RNA Lab Navigator..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Pull latest changes
echo -e "${BLUE}Pulling latest code...${NC}"
git pull origin main

# Rebuild only what changed
echo -e "${BLUE}Rebuilding services...${NC}"
docker-compose -f docker-compose.production.yml build backend frontend-builder

# Apply migrations
echo -e "${BLUE}Applying database migrations...${NC}"
docker-compose -f docker-compose.production.yml exec -T backend python manage.py migrate

# Collect static files
echo -e "${BLUE}Collecting static files...${NC}"
docker-compose -f docker-compose.production.yml exec -T backend python manage.py collectstatic --noinput

# Restart services
echo -e "${BLUE}Restarting services...${NC}"
docker-compose -f docker-compose.production.yml up -d

echo ""
echo -e "${GREEN}✅ Update complete!${NC}"
echo ""
echo "Check logs: docker-compose -f docker-compose.production.yml logs -f"