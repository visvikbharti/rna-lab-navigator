#!/bin/bash
# Script to set up a staging environment and run comprehensive tests

set -e # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}RNA Lab Navigator - Staging Environment Setup${NC}"
echo "=============================================="

# Create staging environment
echo -e "${YELLOW}Step 1: Creating staging environment...${NC}"
mkdir -p staging
cp -r backend staging/
cp -r frontend staging/
cp docker-compose.yml staging/
cp -r nginx staging/
cp -r scripts staging/

# Create staging environment variables
echo -e "${YELLOW}Step 2: Creating staging environment variables...${NC}"
cp backend/.env.example staging/backend/.env
# Generate random secret key for Django
DJANGO_SECRET_KEY=$(python -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))")
# Set staging environment variables
sed -i '' "s/DEBUG=True/DEBUG=False/" staging/backend/.env
sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$DJANGO_SECRET_KEY/" staging/backend/.env

# Set up virtual environment for backend
echo -e "${YELLOW}Step 3: Setting up virtual environment for backend...${NC}"
cd staging/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run backend tests
echo -e "${YELLOW}Step 4: Running backend tests...${NC}"
python -m pytest

# Set up frontend and build
echo -e "${YELLOW}Step 5: Setting up frontend and building...${NC}"
cd ../frontend
npm install
npm run build

# Run frontend tests if they exist
if [ -f "package.json" ] && grep -q "\"test\"" "package.json"; then
    echo -e "${YELLOW}Step 6: Running frontend tests...${NC}"
    npm test
fi

# Start containers in staging environment
echo -e "${YELLOW}Step 7: Starting containers in staging environment...${NC}"
cd ..
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Step 8: Waiting for services to be ready...${NC}"
sleep 10

# Run integration tests
echo -e "${YELLOW}Step 9: Running integration tests...${NC}"
cd backend
source venv/bin/activate
python -m pytest tests/test_integration/test_rag_pipeline.py

# Run performance tests
echo -e "${YELLOW}Step 10: Running performance tests...${NC}"
python -m pytest tests/test_performance/test_rag_performance.py

# Test if response time meets the 5-second KPI
echo -e "${YELLOW}Step 11: Testing response time for the 5-second KPI...${NC}"
start_time=$(date +%s.%N)
curl -s -X POST -H "Content-Type: application/json" -d '{"query": "What is RNA?"}' http://localhost:8000/api/query/
end_time=$(date +%s.%N)
execution_time=$(echo "$end_time - $start_time" | bc)
if (( $(echo "$execution_time > 5.0" | bc -l) )); then
    echo -e "${RED}WARNING: Response time exceeds 5-second KPI. Actual time: ${execution_time} seconds${NC}"
else
    echo -e "${GREEN}Response time meets 5-second KPI. Actual time: ${execution_time} seconds${NC}"
fi

# Clean up
echo -e "${YELLOW}Step 12: Cleaning up...${NC}"
docker-compose down
cd ../..
rm -rf staging

echo -e "${GREEN}Staging environment testing completed!${NC}"
echo "If all tests passed, you can proceed with production deployment."