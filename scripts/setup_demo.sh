#!/bin/bash
# Setup Demo Script for RNA Lab Navigator
# This script sets up and runs the RNA Lab Navigator for demo purposes

set -e  # Exit on error

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}RNA Lab Navigator Demo Setup${NC}"
echo "================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Environment file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please edit it to add your OpenAI API key.${NC}"
    echo ""
    echo -e "${RED}IMPORTANT: You must edit .env and add your OpenAI API key before continuing.${NC}"
    echo "Press Enter when you've updated the .env file..."
    read
else
    echo -e "${GREEN}Environment file exists.${NC}"
fi

# Check for backend .env file
if [ ! -f backend/.env ]; then
    echo -e "${YELLOW}Backend environment file not found. Creating from template...${NC}"
    cp backend/.env.example backend/.env
    
    # Update backend .env with correct host values for Docker
    sed -i '' 's/POSTGRES_HOST=localhost/POSTGRES_HOST=postgres/g' backend/.env
    sed -i '' 's/REDIS_URL=redis:\/\/localhost:6379/REDIS_URL=redis:\/\/redis:6379/g' backend/.env
    sed -i '' 's/WEAVIATE_URL=http:\/\/localhost:8080/WEAVIATE_URL=http:\/\/weaviate:8080/g' backend/.env
    
    # Copy OpenAI API key from root .env
    OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d= -f2)
    if [ ! -z "$OPENAI_API_KEY" ]; then
        sed -i '' "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/g" backend/.env
    fi
    
    echo -e "${GREEN}Created and configured backend/.env file.${NC}"
else
    echo -e "${GREEN}Backend environment file exists.${NC}"
fi

# Check for OpenAI API key
OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d= -f2)
if [ "$OPENAI_API_KEY" = "your-api-key-here" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key" ] || [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}ERROR: OpenAI API key not set in .env file.${NC}"
    echo "Please edit .env and set OPENAI_API_KEY to your OpenAI API key."
    exit 1
fi

# Start Docker services
echo -e "${BLUE}Starting Docker services...${NC}"
docker-compose down
docker-compose up -d
echo -e "${GREEN}Docker services started.${NC}"

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 10

# Check if services are healthy
POSTGRES_HEALTHY=$(docker ps --filter "name=rna_postgres" --format "{{.Status}}" | grep -c "healthy" || echo "0")
REDIS_HEALTHY=$(docker ps --filter "name=rna_redis" --format "{{.Status}}" | grep -c "healthy" || echo "0")
WEAVIATE_RUNNING=$(docker ps --filter "name=rna_weaviate" --format "{{.Status}}" | grep -c "Up" || echo "0")

if [ "$POSTGRES_HEALTHY" -eq "0" ] || [ "$REDIS_HEALTHY" -eq "0" ] || [ "$WEAVIATE_RUNNING" -eq "0" ]; then
    echo -e "${RED}ERROR: Not all services are healthy. Please check docker logs.${NC}"
    exit 1
fi

echo -e "${GREEN}All services are ready.${NC}"

# Set up backend
echo -e "${BLUE}Setting up backend...${NC}"
cd "$PROJECT_DIR/backend"

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser if not exists
echo "Creating superuser (if not exists)..."
DJANGO_SUPERUSER_PASSWORD=admin123 python manage.py createsuperuser --username admin --email admin@example.com --noinput || true

cd "$PROJECT_DIR"

# Set up frontend
echo -e "${BLUE}Setting up frontend...${NC}"
cd "$PROJECT_DIR/frontend"

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

cd "$PROJECT_DIR"

# Display instructions
echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo -e "${BLUE}To ingest sample documents:${NC}"
echo "cd $PROJECT_DIR"
echo "cd backend"
echo "source venv/bin/activate"
echo "python ../scripts/ingest_sample_docs.py --purge"
echo ""
echo -e "${BLUE}To run the backend server:${NC}"
echo "cd $PROJECT_DIR/backend"
echo "source venv/bin/activate"
echo "python manage.py runserver"
echo ""
echo -e "${BLUE}To run Celery worker (in a separate terminal):${NC}"
echo "cd $PROJECT_DIR/backend"
echo "source venv/bin/activate"
echo "celery -A rna_backend worker -l info"
echo ""
echo -e "${BLUE}To run the frontend:${NC}"
echo "cd $PROJECT_DIR/frontend"
echo "npm run dev"
echo ""
echo -e "${BLUE}Access the application:${NC}"
echo "Backend API: http://localhost:8000/api/"
echo "Admin interface: http://localhost:8000/admin/ (username: admin, password: admin123)"
echo "Frontend: http://localhost:5173/"
echo ""
echo -e "${YELLOW}Note: Make sure you ingest the sample documents before trying to query the system.${NC}"
echo ""