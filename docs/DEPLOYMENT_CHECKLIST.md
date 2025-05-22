# RNA Lab Navigator Deployment Checklist

Use this checklist before deploying to production to ensure everything is ready.

## Code Quality

- [ ] All tests are passing (`make test`)
- [ ] Linting checks pass (`make lint`)
- [ ] Code has been reviewed by at least one team member
- [ ] No debug statements or print statements left in the code
- [ ] No sensitive information in the codebase

## Security

- [ ] All environment variables are properly set
- [ ] Strong passwords and secrets are used
- [ ] SSL/TLS certificates are configured
- [ ] Rate limiting is enabled
- [ ] PII detection is enabled
- [ ] Database connection is secure
- [ ] No API keys or credentials committed to the repository

## Performance

- [ ] Response time for queries is under 5 seconds (95th percentile)
- [ ] Memory usage is within acceptable limits
- [ ] CPU usage is within acceptable limits
- [ ] Database connections are optimized
- [ ] Caching is configured properly

## Data

- [ ] Database migrations have been applied
- [ ] Sample data has been loaded
- [ ] Backup system is configured

## Monitoring

- [ ] Logging is configured properly
- [ ] Monitoring alerts are set up
- [ ] Performance metrics are being collected
- [ ] Error reporting is working

## Documentation

- [ ] API documentation is up to date
- [ ] Deployment documentation is complete
- [ ] User guide is available
- [ ] Troubleshooting guide is available

## Rollback Plan

- [ ] There is a clear plan for rolling back in case of issues
- [ ] Database backups are available
- [ ] Previous version of the application is available

## Final Checks

- [ ] The application has been tested in a staging environment
- [ ] All critical paths have been manually tested
- [ ] The deployment process has been documented and tested
- [ ] All team members are aware of the deployment

## Post-Deployment

- [ ] Verify application is running correctly
- [ ] Verify all services are up and running
- [ ] Monitor for any errors or issues
- [ ] Check response times are within expected range
- [ ] Run a few test queries to ensure everything is working

---

Date: __________________

Deployed by: __________________

Version: __________________

Notes: __________________