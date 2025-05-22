# DevOps Documentation for RNA Lab Navigator

This document provides an overview of the DevOps setup for RNA Lab Navigator, including CI/CD pipelines, deployment configurations, monitoring, and operational procedures.

## 1. Infrastructure Overview

RNA Lab Navigator is deployed on a combination of Railway (backend) and Vercel (frontend) platforms with the following components:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Vercel Frontend │◄──────│ Railway Backend  │◄──────│  Database Layer  │
└─────────────────┘       └─────────────────┘       └─────────────────┘
      │                          │                         │
      │                          │                         │
      ▼                          ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    CDN Layer    │       │   Celery Tasks   │       │  Weaviate & Redis│
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### Key Components

- **Frontend**: React application deployed on Vercel
- **Backend**: Django REST API deployed on Railway
- **Database**: PostgreSQL for relational data
- **Vector Database**: Weaviate for document embeddings
- **Cache & Message Broker**: Redis
- **Task Queue**: Celery for background processing
- **Monitoring**: Prometheus, Grafana, and Loki

## 2. CI/CD Pipelines

The repository includes GitHub Actions workflows for continuous integration and deployment:

### Continuous Integration (CI)

Triggered on:
- Pull requests to `main`/`master` branches
- Push to `main`/`master`/`dev` branches

Pipeline steps:
1. **Backend Tests**: Run Django tests, linting, and coverage
2. **Frontend Tests**: Run React tests, linting, and coverage
3. **Security Scan**: Run security analysis tools (Bandit, Safety, npm audit)
4. **Build Test**: Build Docker images for backend and frontend

### Continuous Deployment (CD)

Triggered on:
- Push to `main`/`master` branches (staging)
- Tags starting with `v` (production)

Pipeline steps:
1. **Deploy to Staging**: Automatically deploy to staging environment
2. **Smoke Tests**: Run basic health checks on staging
3. **Deploy to Production**: Deploy to production when using tag-based release
4. **Create GitHub Release**: Create a release with changelog
5. **Production Validation**: Verify production deployment

## 3. Environment Setup

### Development Environment

Development environment can be started using Docker Compose:

```bash
docker-compose up -d                 # pg + redis + weaviate
cd backend && make dev               # venv, deps, migrate, runserver
# in two extra terminals
celery -A rna_backend worker -l info
celery -A rna_backend beat   -l info
cd ../frontend && npm i && npm run dev
```

### Staging Environment

The staging environment is deployed automatically on Railway and Vercel when changes are pushed to the `main`/`master` branch. Configuration is loaded from environment variables stored in the respective platforms.

### Production Environment

Production is deployed when a version tag (e.g., `v1.0.0`) is pushed. For a production-like environment on your own infrastructure, you can use:

```bash
# Set the version tag
export TAG=1.0.0

# Start the production stack
docker-compose -f docker-compose.prod.yml up -d
```

## 4. Deployment Configuration

### Docker Configuration

- **Backend Dockerfile**: Multi-stage build with Python dependencies
- **Frontend Dockerfile**: Multi-stage build with Nginx for static file serving
- **Nginx Config**: Reverse proxy with caching, compression, and security headers
- **Docker Compose**: Services definition for complete stack deployment

### Environment Variables

Key environment variables for deployment:

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_*` | Database connection details | `POSTGRES_PASSWORD=secure_password` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `WEAVIATE_URL` | Weaviate connection URL | `http://weaviate:8080` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `LLM_NETWORK_ISOLATION` | Enable local LLM mode | `True` |
| `SECRET_KEY` | Django secret key | `random_secure_string` |
| `DEBUG` | Enable debug mode | `False` in production |

## 5. Monitoring & Observability

### Metrics Collection

- **Prometheus**: Collects metrics from all services
- **Grafana**: Visualizes metrics and provides dashboards
- **Loki**: Collects and indexes logs
- **Promtail**: Forwards logs to Loki

### Available Dashboards

1. **System Overview**: CPU, memory, request rates
2. **API Performance**: Response times, error rates, endpoints
3. **Security Monitoring**: Auth attempts, WAF blocks, rate limits
4. **Search Quality**: Query performance, embedding metrics

### Health Checks

Health checks are implemented for all services:

- **Backend**: `/api/health/` endpoint
- **Frontend**: `/health` endpoint
- **Database**: Connection check
- **Weaviate**: Readiness endpoint

## 6. Backup & Restore

Automated backup procedures are implemented through Celery tasks:

### Backup Schedule

- **PostgreSQL**: Daily at 2:00 AM
- **Weaviate**: Daily at 3:00 AM
- **Media Files**: Daily at 4:00 AM
- **Full System**: Weekly on Sunday at 1:00 AM

### Backup Storage

Backups can be stored:
- Locally in `./backend/backups/`
- Remote S3-compatible storage (recommended for production)

### Backup Retention

- Default retention is 7 days
- Configurable via `BACKUP_RETENTION_DAYS` environment variable

## 7. Scaling Considerations

### Horizontal Scaling

- **Backend**: Can be scaled horizontally behind load balancer
- **Celery Workers**: Can be scaled independently based on workload
- **Databases**: Require replication/clustering setup

### Resource Scaling

For medium load (50 concurrent users):
- **Backend**: 2 CPUs, 2GB RAM
- **Celery**: 2 CPUs, 2GB RAM
- **PostgreSQL**: 2 CPUs, 4GB RAM
- **Weaviate**: 4 CPUs, 8GB RAM

### Performance Optimization

- **Caching**: Implemented at multiple levels (Redis, Nginx)
- **Database Indexes**: Optimized for common queries
- **Connection Pooling**: Configured for database connections
- **Static Files**: Served through CDN with appropriate caching

## 8. Security Considerations

### Network Security

- All services in private network except explicit public endpoints
- mTLS for Weaviate communication
- Rate limiting on API endpoints

### Update Management

- Dependencies updated through CI pipeline
- Security scanning performed on each build
- Critical vulnerabilities trigger alerts

### Secrets Management

- Environment-based secrets storage
- No secrets in code or images
- Secrets rotation procedures

## 9. Disaster Recovery

### Recovery Process

In case of service disruption:

1. Identify affected components using monitoring
2. Check logs for error patterns
3. Restore affected services:
   - For code issues: Rollback to previous version
   - For data issues: Restore from backup

### Recovery Testing

- Regular backup restoration testing
- Failover scenario practice
- Documented recovery procedures

## 10. Common Operations

### Deployment

```bash
# Deploy to staging
git push origin main

# Deploy to production
git tag v1.0.0
git push origin v1.0.0
```

### Database Migrations

```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate
```

### Logs Access

```bash
# View backend logs
docker logs rna-lab-backend

# View all logs in Grafana Loki
# Access Grafana at http://localhost:3000
```

### Service Restart

```bash
# Restart specific service
docker-compose -f docker-compose.prod.yml restart <service_name>

# Restart entire stack
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## 11. Troubleshooting Guide

### Common Issues

| Issue | Possible Cause | Resolution |
|-------|----------------|------------|
| Backend 500 errors | Database connection | Check DB connectivity and logs |
| Slow queries | Missing index or large dataset | Review query performance |
| Celery tasks stuck | Redis connectivity | Check Redis connection and restart workers |
| Out of memory | Large document processing | Increase container memory limits |

### Diagnostic Commands

```bash
# Check system health
curl https://api.example.com/api/health/

# Test database connection
docker exec rna-backend python -c "from django.db import connection; connection.ensure_connection()"

# Check Celery queue status
docker exec rna-celery celery -A rna_backend inspect active
```

## 12. Contact & Support

- **Technical Contact**: [tech@example.com](mailto:tech@example.com)
- **Emergency Support**: +1-555-123-4567
- **Bug Reports**: GitHub Issues

---

This documentation is maintained by the RNA Lab Navigator development team.