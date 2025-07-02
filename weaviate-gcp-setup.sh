#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Weaviate Setup for Google Cloud Platform${NC}"
echo "========================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed.${NC}"
    exit 1
fi

# Get project info
PROJECT_ID=$(gcloud config get-value project)
read -p "Enter your preferred zone for Weaviate (default: asia-south1-a): " ZONE
ZONE=${ZONE:-asia-south1-a}

echo -e "${YELLOW}Option 1: Deploy Weaviate on Compute Engine (Recommended for prototype)${NC}"
echo "This will create a single VM instance with Weaviate"
echo ""
echo -e "${YELLOW}Option 2: Deploy Weaviate on GKE (For production scale)${NC}"
echo "This will create a Kubernetes cluster with Weaviate"
echo ""
read -p "Choose option (1 or 2): " OPTION

if [ "$OPTION" == "1" ]; then
    # Compute Engine deployment
    echo -e "${YELLOW}Creating Compute Engine instance for Weaviate...${NC}"
    
    gcloud compute instances create weaviate-instance \
        --zone=$ZONE \
        --machine-type=e2-medium \
        --boot-disk-size=50GB \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --tags=weaviate-server \
        --metadata=startup-script='#!/bin/bash
# Update system
apt-get update
apt-get install -y docker.io docker-compose

# Create Weaviate docker-compose file
cat > /opt/weaviate-docker-compose.yml << EOF
version: "3.4"
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - 8080:8080
    restart: always
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      DEFAULT_VECTORIZER_MODULE: "text2vec-openai"
      ENABLE_MODULES: "text2vec-openai,generative-openai"
      CLUSTER_HOSTNAME: "weaviate"
    volumes:
      - /var/lib/weaviate:/var/lib/weaviate
EOF

# Start Weaviate
cd /opt
docker-compose -f weaviate-docker-compose.yml up -d
'

    # Create firewall rule
    echo -e "${YELLOW}Creating firewall rule...${NC}"
    gcloud compute firewall-rules create allow-weaviate \
        --allow=tcp:8080 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=weaviate-server || true

    # Get instance IP
    sleep 30  # Wait for instance to start
    WEAVIATE_IP=$(gcloud compute instances describe weaviate-instance \
        --zone=$ZONE \
        --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

    echo -e "${GREEN}Weaviate instance created!${NC}"
    echo "Weaviate URL: http://$WEAVIATE_IP:8080"
    echo ""
    echo "To make it more secure:"
    echo "1. Set up Cloud Load Balancer with SSL"
    echo "2. Configure authentication in Weaviate"
    echo "3. Restrict firewall rules to specific IPs"

elif [ "$OPTION" == "2" ]; then
    # GKE deployment
    echo -e "${YELLOW}Creating GKE cluster...${NC}"
    
    CLUSTER_NAME="rna-lab-cluster"
    REGION=$(echo $ZONE | cut -d'-' -f1-2)
    
    gcloud container clusters create $CLUSTER_NAME \
        --zone=$ZONE \
        --num-nodes=2 \
        --machine-type=e2-standard-2 \
        --disk-size=50 \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=3

    # Get cluster credentials
    gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE

    # Install Weaviate using Helm
    echo -e "${YELLOW}Installing Helm...${NC}"
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

    echo -e "${YELLOW}Installing Weaviate...${NC}"
    helm repo add weaviate https://weaviate.github.io/weaviate-helm
    helm repo update

    # Create values file
    cat > weaviate-values.yaml << EOF
replicas: 1
image:
  tag: latest
env:
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: true
  DEFAULT_VECTORIZER_MODULE: text2vec-openai
  ENABLE_MODULES: text2vec-openai,generative-openai
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
persistence:
  enabled: true
  size: 30Gi
service:
  type: LoadBalancer
EOF

    helm install weaviate weaviate/weaviate -f weaviate-values.yaml

    echo -e "${YELLOW}Waiting for LoadBalancer IP...${NC}"
    sleep 60
    
    WEAVIATE_IP=$(kubectl get svc weaviate -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    echo -e "${GREEN}Weaviate deployed on GKE!${NC}"
    echo "Weaviate URL: http://$WEAVIATE_IP"
fi

echo ""
echo "Next steps:"
echo "1. Update Cloud Run environment variable: WEAVIATE_URL=http://$WEAVIATE_IP:8080"
echo "2. Test connection: curl http://$WEAVIATE_IP:8080/v1/meta"
echo "3. Configure Weaviate authentication for production"