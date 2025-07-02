# Google Cloud Platform Deployment Guide

This guide walks you through deploying the RNA Lab Navigator on Google Cloud Platform.

## Prerequisites

1. Google Cloud account with billing enabled
2. `gcloud` CLI installed ([Install Guide](https://cloud.google.com/sdk/docs/install))
3. Docker installed locally (for testing)
4. Your OpenAI API key

## Quick Deployment

### 1. Clone and Navigate
```bash
git clone https://github.com/visvikbharti/rna-lab-navigator.git
cd rna-lab-navigator
```

### 2. Run Setup Script
```bash
./gcp-setup.sh
```

This script will:
- Enable required GCP APIs
- Create Cloud SQL (PostgreSQL) instance
- Create Memorystore (Redis) instance
- Create Cloud Storage buckets
- Set up Secret Manager
- Build and deploy to Cloud Run

### 3. Deploy Weaviate
```bash
./weaviate-gcp-setup.sh
```

Choose Option 1 (Compute Engine) for the prototype.

### 4. Update Frontend
Update your frontend environment:
```bash
cd frontend
echo "VITE_API_BASE_URL=YOUR_CLOUD_RUN_URL/api" > .env.production
```

Then redeploy to Vercel:
```bash
vercel --prod
```

## Architecture on GCP

- **Backend**: Cloud Run (serverless, auto-scaling)
- **Database**: Cloud SQL (managed PostgreSQL)
- **Cache**: Memorystore (managed Redis)
- **Vector DB**: Weaviate on Compute Engine
- **Storage**: Cloud Storage (for media files)
- **Secrets**: Secret Manager
- **Frontend**: Vercel (unchanged)

## Costs Estimate (Monthly)

For a 21-member lab:
- Cloud Run: ~$10-30 (pay per request)
- Cloud SQL (db-f1-micro): ~$10
- Memorystore (1GB): ~$35
- Compute Engine (e2-medium): ~$25
- Cloud Storage: ~$5
- **Total**: ~$85-105/month

## Security Features

1. **Network Security**
   - Private VPC for backend services
   - Cloud SQL uses private IP
   - Firewall rules restrict access

2. **Authentication**
   - Service accounts with minimal permissions
   - Secrets stored in Secret Manager
   - JWT tokens for API authentication

3. **Data Security**
   - Encrypted at rest and in transit
   - Regular automated backups
   - Access logs in Cloud Logging

## Management Commands

### View Logs
```bash
gcloud run logs read --service=rna-lab-backend
```

### Update Environment Variables
```bash
gcloud run services update rna-lab-backend \
  --set-env-vars KEY=VALUE
```

### Connect to Database
```bash
gcloud sql connect rna-lab-db --user=rna_lab_user
```

### SSH to Weaviate Instance
```bash
gcloud compute ssh weaviate-instance --zone=asia-south1-a
```

## Monitoring

1. **Cloud Console**: https://console.cloud.google.com
2. **Metrics**: Cloud Run metrics, SQL metrics
3. **Alerts**: Set up in Cloud Monitoring
4. **Logs**: Cloud Logging for all services

## Troubleshooting

### 503 Service Unavailable
- Check Cloud Run logs
- Verify database connection
- Check Redis connection

### CORS Errors
- Update CORS_ALLOWED_ORIGINS in Cloud Run env vars
- Ensure frontend URL is whitelisted

### Database Connection Failed
- Check Cloud SQL is running
- Verify service account permissions
- Check VPC connector settings

### Weaviate Connection Failed
- Verify Compute Engine instance is running
- Check firewall rules
- Test with: `curl http://WEAVIATE_IP:8080/v1/meta`

## Support

For issues specific to:
- GCP setup: Check Cloud Console logs
- Application bugs: Create GitHub issue
- Weaviate: Check Weaviate logs on the instance