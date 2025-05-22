# 🚀 Railway & Vercel Deployment Checklist

## Pre-Deployment Setup

### Prerequisites
- [ ] Railway CLI installed (`curl -fsSL https://railway.app/install.sh | sh`)
- [ ] Vercel CLI installed (`npm install -g vercel`)
- [ ] OpenAI API key obtained
- [ ] Git repository cloned locally
- [ ] Node.js and Python installed

### Environment Variables Prepared
- [ ] `SECRET_KEY` - Strong Django secret key generated
- [ ] `OPENAI_API_KEY` - Valid OpenAI API key with sufficient credits
- [ ] Frontend URL known for CORS configuration

## Backend Deployment (Railway)

### Service Creation
- [ ] Main backend service created
- [ ] PostgreSQL database added
- [ ] Redis cache added
- [ ] Weaviate vector database deployed
- [ ] Celery worker service created
- [ ] Celery beat service created (optional)

### Configuration
- [ ] Environment variables set in Railway dashboard
- [ ] Domain configured (if using custom domain)
- [ ] SSL certificates active
- [ ] Health checks configured

### Database Setup
- [ ] Migrations applied successfully
- [ ] Static files collected
- [ ] Initial data loaded (optional)
- [ ] Sample documents ingested (optional)

### Service Verification
- [ ] Main backend health check passes: `/health/`
- [ ] Detailed health check passes: `/health/detailed/`
- [ ] API endpoints responding: `/api/query/`
- [ ] Admin panel accessible: `/admin/`
- [ ] Static files serving correctly

## Frontend Deployment (Vercel)

### Project Setup
- [ ] Vercel project created and linked
- [ ] Build configuration verified
- [ ] Environment variables set
- [ ] Custom domain configured (optional)

### Configuration
- [ ] `VITE_API_BASE_URL` points to Railway backend
- [ ] Production build successful
- [ ] Security headers configured
- [ ] Caching rules set

### Verification
- [ ] Frontend loads without errors
- [ ] API connection successful
- [ ] Search functionality works
- [ ] File upload works (if enabled)
- [ ] Navigation works correctly

## Integration Testing

### CORS Configuration
- [ ] Backend CORS settings include frontend URL
- [ ] Preflight requests work correctly
- [ ] Authentication flows work
- [ ] File uploads work across domains

### Full Pipeline Test
- [ ] Document upload successful
- [ ] Document processing works
- [ ] Search returns relevant results
- [ ] Citations display correctly
- [ ] Feedback system works

## Security Configuration

### Backend Security
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` set
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] Security headers enabled
- [ ] Rate limiting active
- [ ] PII scanning enabled
- [ ] WAF configured (if enabled)

### Frontend Security
- [ ] Security headers configured
- [ ] Content Security Policy set
- [ ] No sensitive data in client-side code
- [ ] HTTPS enforced

## Monitoring & Maintenance

### Logging
- [ ] Application logs accessible
- [ ] Error reporting configured
- [ ] Security events logged
- [ ] Performance metrics tracked

### Backup & Recovery
- [ ] Database backup scheduled
- [ ] Media files backup configured
- [ ] Recovery procedures documented
- [ ] Backup restoration tested

### Performance
- [ ] Response times acceptable (<5s target)
- [ ] Resource usage monitored
- [ ] Scaling thresholds set
- [ ] CDN configured (if needed)

## Production Readiness

### Documentation
- [ ] API documentation updated
- [ ] User guide created
- [ ] Admin procedures documented
- [ ] Troubleshooting guide available

### Access & Permissions
- [ ] Admin accounts created
- [ ] User permissions configured
- [ ] API access controls set
- [ ] Service account credentials secured

### Final Verification
- [ ] Load testing performed
- [ ] Security scan completed
- [ ] All stakeholders notified
- [ ] Rollback plan documented

## Post-Deployment Tasks

### Week 1
- [ ] Monitor application stability
- [ ] Check error rates and logs
- [ ] Verify backup systems
- [ ] Gather initial user feedback

### Week 2-4
- [ ] Performance optimization
- [ ] User training and onboarding
- [ ] Documentation updates
- [ ] Feature requests collection

### Monthly
- [ ] Security updates applied
- [ ] Dependency updates
- [ ] Performance review
- [ ] Cost optimization review

## Emergency Procedures

### Rollback Plan
- [ ] Previous version backup available
- [ ] Rollback procedure documented
- [ ] Database rollback strategy defined
- [ ] Emergency contacts list updated

### Incident Response
- [ ] Monitoring alerts configured
- [ ] On-call procedures defined
- [ ] Communication plan established
- [ ] Recovery time objectives defined

## Success Metrics

### Performance Targets
- [ ] Search response time <5 seconds
- [ ] API availability >99.5%
- [ ] Error rate <1%
- [ ] User satisfaction >85%

### Business Metrics
- [ ] Daily active users tracked
- [ ] Search query success rate monitored
- [ ] Document processing throughput measured
- [ ] User engagement metrics collected

---

## Quick Commands Reference

### Health Checks
```bash
# Backend health
curl https://your-backend.railway.app/health/

# Detailed health
curl https://your-backend.railway.app/health/detailed/

# Frontend
curl https://your-frontend.vercel.app/
```

### Deployment
```bash
# Complete deployment
./scripts/deploy-complete.sh

# Backend only
./scripts/deploy-railway.sh

# Frontend only
./scripts/deploy-vercel.sh --prod
```

### Monitoring
```bash
# Backend logs
railway logs --follow

# Service status
railway status

# Vercel logs
vercel logs your-deployment-url
```

---

**✅ Deployment Complete!** 

Your RNA Lab Navigator is now live and ready for production use! 🎉