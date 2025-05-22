# RNA Lab Navigator Analytics

This module provides comprehensive analytics, audit logging, and monitoring capabilities for the RNA Lab Navigator system.

## Features

- **Usage Metrics**: Track user queries, response times, and system load
- **Security Auditing**: Log security-relevant events and monitor suspicious activities
- **Performance Monitoring**: Track system component health and performance over time
- **Query Analytics**: Analyze patterns in user queries to improve the system
- **Interactive Dashboard**: Visualize metrics in the Django admin interface

## Architecture

The analytics system consists of the following components:

1. **Data Collection**:
   - Middleware for capturing request/response data
   - Hooks in key system components for event logging
   - System performance monitoring

2. **Data Storage**:
   - Raw metrics tables for detailed analysis
   - Daily aggregated metrics for efficient reporting
   - Event logs for security and audit purposes

3. **Data Processing**:
   - Scheduled tasks for aggregating and analyzing metrics
   - Automated report generation
   - Data retention policy enforcement

4. **Visualization**:
   - Admin dashboard for viewing metrics
   - API endpoints for custom dashboards
   - Exportable reports

## Models

- `SystemMetric`: Raw performance metrics (response time, CPU, memory, etc.)
- `AuditEvent`: Security and compliance audit events
- `UserActivityLog`: Detailed user activity tracking
- `DailyMetricAggregate`: Daily aggregated metrics for efficient reporting
- `QueryTypeAggregate`: Analysis of query patterns and categories
- `SecurityEvent`: Detailed security event tracking
- `SystemStatusLog`: System health monitoring

## Configuration

Analytics settings are configured in `settings.py`:

```python
# Analytics settings
ANALYTICS_ENABLED = True
ANALYTICS_RETENTION_DAYS = 90  # Days to keep raw analytics data
ANALYTICS_MONITOR_SYSTEM = True  # Enable system performance monitoring
ANALYTICS_SENSITIVE_PATHS = [
    '/admin/',
    '/api/auth/',
    '/api/users/',
]  # Paths containing sensitive operations to audit
```

## Scheduled Tasks

Scheduled tasks (via Celery) handle data aggregation and maintenance:

- `aggregate_daily_metrics`: Aggregates metrics daily (runs at 1 AM)
- `generate_weekly_report`: Generates weekly summary report (runs Monday 1:30 AM)
- `monitor_system_performance`: Collects system performance metrics (every 15 minutes)
- `cleanup_old_metrics`: Removes old raw metrics to prevent database bloat (runs monthly)

## Getting Started

1. Ensure the analytics app is included in `INSTALLED_APPS`:
   ```python
   INSTALLED_APPS = [
       # ...
       "api.analytics",
   ]
   ```

2. Add the analytics middleware to `MIDDLEWARE`:
   ```python
   MIDDLEWARE = [
       # ...
       "api.analytics.middleware.AnalyticsMiddleware",
   ]
   ```

3. Initialize the analytics database (for development):
   ```bash
   python manage.py initialize_analytics --with-sample-data
   ```

4. Access the dashboard at `/admin/api/analytics/dailymetricaggregate/dashboard/`

## API Endpoints

The analytics module provides the following API endpoints:

- `api/analytics/dashboard/data/`: Dashboard summary data
- `api/analytics/system/health/`: System health metrics
- `api/analytics/queries/analytics/`: Query pattern analytics
- `api/analytics/security/analytics/`: Security event analytics

All endpoints require admin privileges to access.

## Security Considerations

- Access to analytics data is restricted to admin users
- Sensitive data is filtered from logs (see `ANALYTICS_SENSITIVE_PATHS`)
- Personal information is not stored in analytics data
- Raw metrics are automatically purged after the retention period