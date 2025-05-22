#!/bin/bash
# Production deployment script for RNA Lab Navigator

set -e # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/your-organization/rna-lab-navigator.git"
DEPLOY_DIR="/opt/rna-lab-navigator"
BACKUP_DIR="/opt/backups/rna-lab-navigator"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}RNA Lab Navigator - Production Deployment${NC}"
echo "==========================================\n"

# Check if we're running on a production server
if [ ! -d "$DEPLOY_DIR" ]; then
    echo -e "${YELLOW}Creating deployment directory at $DEPLOY_DIR${NC}"
    sudo mkdir -p $DEPLOY_DIR
    sudo chown $USER:$USER $DEPLOY_DIR
fi

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Creating backup directory at $BACKUP_DIR${NC}"
    sudo mkdir -p $BACKUP_DIR
    sudo chown $USER:$USER $BACKUP_DIR
fi

# Step 1: Check if deploy directory exists and contains a git repo
echo -e "${YELLOW}Step 1: Preparing deployment directory...${NC}"
if [ -d "$DEPLOY_DIR/.git" ]; then
    echo "Repository exists, updating..."
    cd $DEPLOY_DIR
    git fetch
    # Create a backup of the current version
    echo "Creating backup of current version..."
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py backup_data --output="${BACKUP_DIR}/backup_${TIMESTAMP}.zip" || true
    git pull
else
    echo "Fresh install, cloning repository..."
    cd $DEPLOY_DIR
    git clone $REPO_URL .
fi

# Step 2: Check if environment variables are set
echo -e "${YELLOW}Step 2: Checking environment variables...${NC}"
if [ ! -f "$DEPLOY_DIR/backend/.env.production" ]; then
    echo -e "${RED}ERROR: Production environment variables not found!${NC}"
    echo "Please create backend/.env.production before deploying."
    exit 1
fi

# Step 3: Run all tests
echo -e "${YELLOW}Step 3: Running tests...${NC}"
cd $DEPLOY_DIR
make test || {
    echo -e "${RED}Tests failed! Proceed anyway? (y/n)${NC}"
    read proceed
    if [ "$proceed" != "y" ]; then
        echo "Deployment aborted."
        exit 1
    fi
}

# Step 4: Build and deploy
echo -e "${YELLOW}Step 4: Building and deploying...${NC}"
cd $DEPLOY_DIR
make prod-build

# Stop and remove existing containers if they exist
make prod-down || true

# Start the new containers
make prod-up

# Step 5: Run database migrations
echo -e "${YELLOW}Step 5: Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

# Step 6: Collect static files
echo -e "${YELLOW}Step 6: Collecting static files...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

# Step 7: Verify deployment
echo -e "${YELLOW}Step 7: Verifying deployment...${NC}"
if curl -s http://localhost:80/api/health/ | grep -q "ok"; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${RED}WARNING: Health check failed!${NC}"
    echo "Please check the logs with: make prod-logs"
fi

# Step 8: Initialize analytics if needed
echo -e "${YELLOW}Step 8: Initializing analytics...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py initialize_analytics || true

# Step 9: Final steps
echo -e "${YELLOW}Step 9: Running final steps...${NC}"
echo "Deployment completed at $(date)"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "You can view the logs with: make prod-logs"
echo "Access the application at: http://your-domain.com"
echo "Access the admin interface at: http://your-domain.com/admin"