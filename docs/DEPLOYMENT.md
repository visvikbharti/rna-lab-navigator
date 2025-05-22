# RNA Lab Navigator Deployment Guide

This document provides step-by-step instructions for deploying the RNA Lab Navigator system to a production environment. Follow these instructions carefully to ensure a smooth deployment.

## Prerequisites

Before beginning deployment, ensure you have:

1. A Linux server with Docker and Docker Compose installed
2. At least 4GB RAM available for the application
3. At least 20GB of disk space
4. Domain name(s) pointing to your server (e.g., rna-lab-navigator.example.com)
5. OpenAI API key for GPT-4o and Ada-002 embeddings

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/rna-lab-navigator.git
cd rna-lab-navigator
```

### 2. Configure Environment Variables

Create production environment variables by copying the template:

```bash
cp backend/.env.production.example backend/.env.production
```

Generate secure random values for the environment variables:

```bash
python scripts/generate_env_values.py
```

Edit `backend/.env.production` and add the generated values.

**Important**: Make sure to fill in:
- `OPENAI_API_KEY` - Your OpenAI API key
- `ALLOWED_HOSTS` - Your domain name(s)
- `SITE_URL` - Your primary domain name with https protocol

### 3. SSL Certificates (If Not Using a Reverse Proxy)

If you're not using a separate reverse proxy, set up SSL certificates:

```bash
mkdir -p nginx/ssl
# Place your SSL certificates in this directory:
# - nginx/ssl/cert.pem
# - nginx/ssl/key.pem
```

If you're using Let's Encrypt, you can use the certbot Docker container to obtain certificates.

### 4. Build and Start the Application

```bash
make deploy
```

This will:
1. Run linting checks
2. Run tests
3. Build the frontend assets
4. Build the Docker images
5. Start all the services

### 5. Verify the Deployment

Check that all services are running:

```bash
docker-compose -f docker-compose.prod.yml ps
```

View the logs to check for any errors:

```bash
make prod-logs
```

### 6. Initial Data Setup

Load sample data into the system:

```bash
docker-compose -f docker-compose.prod.yml exec backend python scripts/ingest_sample_docs.py
```

### 7. Create Superuser

Create an admin user to access the Django admin interface:

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## Railway Deployment

If deploying to Railway, follow these additional steps:

1. Install the Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Link to your Railway project:
   ```bash
   railway link
   ```

4. Deploy the application:
   ```bash
   railway up
   ```

## Vercel Frontend Deployment

For deploying the frontend separately to Vercel:

1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

3. Deploy to Vercel:
   ```bash
   vercel --prod
   ```

## Monitoring

The production setup includes:

- Prometheus for metrics collection
- Grafana for visualization
- Loki for log aggregation

Access the monitoring dashboard at `https://your-domain.com/grafana` with the username `admin` and the password set in your environment variables.

## Backup and Recovery

Regular backups are configured to run daily. You can manually trigger a backup with:

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py backup_data
```

To restore from a backup:

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py restore_backup backup_file.zip
```

## Troubleshooting

If you encounter issues during deployment, check:

1. Docker logs for specific service errors
2. Network connectivity between services
3. Environment variable configuration
4. Disk space and memory usage

For further assistance, please contact the development team.

---

Last updated: May 2025