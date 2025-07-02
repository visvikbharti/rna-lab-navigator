#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}RNA Lab Navigator - Google Cloud Platform Setup${NC}"
echo "================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed.${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project variables
read -p "Enter your GCP Project ID: " PROJECT_ID
read -p "Enter your preferred region (default: asia-south1): " REGION
REGION=${REGION:-asia-south1}

# Set the project
echo -e "${YELLOW}Setting up GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    cloudresourcemanager.googleapis.com \
    container.googleapis.com \
    compute.googleapis.com

# Create service account
echo -e "${YELLOW}Creating service account...${NC}"
gcloud iam service-accounts create rna-lab-backend \
    --display-name="RNA Lab Backend Service Account" \
    --description="Service account for RNA Lab Navigator backend" || true

# Grant necessary permissions
echo -e "${YELLOW}Granting permissions...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:rna-lab-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:rna-lab-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:rna-lab-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create Cloud SQL instance
echo -e "${YELLOW}Creating Cloud SQL instance (this may take 5-10 minutes)...${NC}"
gcloud sql instances create rna-lab-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=$REGION \
    --network=default \
    --no-assign-ip || echo "Cloud SQL instance already exists"

# Create database and user
echo -e "${YELLOW}Creating database and user...${NC}"
gcloud sql databases create rna_lab_navigator \
    --instance=rna-lab-db || echo "Database already exists"

# Generate a secure password
DB_PASSWORD=$(openssl rand -base64 32)

# Create database user
gcloud sql users create rna_lab_user \
    --instance=rna-lab-db \
    --password=$DB_PASSWORD || echo "User already exists"

# Create Redis instance (Memorystore)
echo -e "${YELLOW}Creating Redis instance (this may take 5-10 minutes)...${NC}"
gcloud redis instances create rna-lab-redis \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_6_x || echo "Redis instance already exists"

# Get Redis host
REDIS_HOST=$(gcloud redis instances describe rna-lab-redis --region=$REGION --format="value(host)")

# Create Cloud Storage buckets
echo -e "${YELLOW}Creating Cloud Storage buckets...${NC}"
gsutil mb -p $PROJECT_ID -c standard -l $REGION gs://${PROJECT_ID}-static/ || true
gsutil mb -p $PROJECT_ID -c standard -l $REGION gs://${PROJECT_ID}-media/ || true

# Set bucket permissions
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}-static/
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}-media/

# Create secrets in Secret Manager
echo -e "${YELLOW}Creating secrets...${NC}"

# Django secret key
DJANGO_SECRET=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
echo -n "$DJANGO_SECRET" | gcloud secrets create django-secret-key --data-file=- || echo "Secret already exists"

# Database password
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=- || echo "Secret already exists"

# OpenAI API key
read -s -p "Enter your OpenAI API key: " OPENAI_KEY
echo
echo -n "$OPENAI_KEY" | gcloud secrets create openai-api-key --data-file=- || echo "Secret already exists"

# Build and deploy
echo -e "${YELLOW}Building and deploying to Cloud Run...${NC}"
gcloud builds submit --config backend/cloudbuild.yaml

# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe rna-lab-backend --region=$REGION --format="value(status.url)")

echo -e "${GREEN}Setup completed successfully!${NC}"
echo "================================================"
echo "Cloud Run URL: $SERVICE_URL"
echo "Redis Host: $REDIS_HOST"
echo ""
echo "Next steps:"
echo "1. Update your frontend .env with: VITE_API_BASE_URL=$SERVICE_URL/api"
echo "2. Add $SERVICE_URL to CORS_ALLOWED_ORIGINS in Cloud Run environment variables"
echo "3. Deploy Weaviate separately (see weaviate-gcp-setup.sh)"
echo ""
echo "To manage your deployment:"
echo "- View logs: gcloud run logs read --service=rna-lab-backend"
echo "- Update env vars: gcloud run services update rna-lab-backend --set-env-vars KEY=VALUE"
echo "- Access database: gcloud sql connect rna-lab-db --user=rna_lab_user"