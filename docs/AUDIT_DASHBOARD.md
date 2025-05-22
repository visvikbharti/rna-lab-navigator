# RNA Lab Navigator Audit Dashboard

## Overview

The Audit Dashboard provides comprehensive monitoring, analytics, and security auditing capabilities for the RNA Lab Navigator system. It enables administrators to track system performance, monitor usage patterns, detect security issues, and generate compliance reports.

## Features

### 1. Real-time System Monitoring

- **System Performance Metrics**: CPU, memory, disk usage, and response times
- **Component Health Status**: Real-time status of all system components (API, database, vector DB, Celery, Redis, LLM)
- **WebSocket-based Updates**: Live updates without page refresh

### 2. User Activity Tracking

- **Query Analytics**: Track query patterns, response times, and user behavior
- **Document Usage**: Monitor which documents and protocols are most accessed
- **User Session Analysis**: Track session duration and activity patterns

### 3. Security Auditing

- **Security Event Logging**: Comprehensive logging of security-relevant events
- **PII Detection Alerts**: Notification when personal information is detected
- **Authentication Events**: Track login attempts, successes, and failures

### 4. Data Aggregation

- **Daily Metrics**: Aggregated daily statistics for efficient reporting
- **Query Type Analysis**: Categorization and analysis of query patterns
- **Performance Trends**: Track system performance over time

### 5. Visualization

- **Interactive Charts**: Visual representation of metrics and trends
- **Component Status Dashboard**: Visual overview of system health
- **Customizable Time Ranges**: View data over different time periods

## Architecture

The Audit Dashboard is built on a layered architecture:

1. **Data Collection Layer**:
   - `AnalyticsMiddleware`: Captures request/response data
   - `Collector` classes: Specialized data collectors for different metrics
   - Hooks and decorators for instrumenting core functions

2. **Data Storage Layer**:
   - Efficient database models for metrics and events
   - Time-series storage for performance data
   - JSON fields for flexible metadata

3. **Data Processing Layer**:
   - `MetricsAggregator`: Processes raw data into aggregated metrics
   - Scheduled tasks for periodic aggregation and analysis
   - Background monitoring for system health

4. **Presentation Layer**:
   - Admin dashboard for visualizing metrics
   - WebSocket consumers for real-time updates
   - API endpoints for integration with external tools

## Usage

### Accessing the Dashboard

The Audit Dashboard is accessible to admin users at:

```
/admin/api/analytics/dailymetricaggregate/dashboard/
```

### Running Monitoring Commands

The system includes management commands for manual monitoring:

```bash
# Basic system health check
python manage.py monitor_system

# Continuous monitoring with 30-second updates
python manage.py monitor_system --watch --interval 30

# Start background monitoring daemon
python manage.py monitor_system --daemon

# Generate and export metrics as JSON
python manage.py monitor_system --metrics-only --json > metrics.json
```

### Scheduled Tasks

The following tasks run automatically according to schedule:

- **Daily Aggregation**: Runs at 1 AM to aggregate the previous day's metrics
- **Weekly Report Generation**: Runs Mondays at 1:30 AM
- **System Monitoring**: Runs every 15 minutes
- **Old Data Cleanup**: Runs monthly to purge outdated raw metrics

## Integration Points

The Audit Dashboard integrates with:

1. **Django Admin**: Custom admin views for data visualization
2. **Security Features**: Hooks into PII detection and security monitoring
3. **Core System Components**: Instrumented key functions with performance tracking
4. **Celery Beat**: Scheduled tasks for data processing

## Security Considerations

- **Access Control**: Dashboard is restricted to admin users only
- **Data Protection**: Sensitive data is filtered from logs
- **Audit Trail**: Complete audit trail for compliance requirements
- **Data Retention**: Configurable retention periods for compliance

## Performance Impact

The Audit Dashboard is designed for minimal performance impact:

- Middleware optimized for low overhead (< 5ms per request)
- Bulk operations for efficient data storage
- Aggregation performed during off-peak hours
- Background monitoring in separate thread
- Configurable sampling rates for high-volume metrics

## Configuration

Configuration options in `settings.py`:

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

## Future Enhancements

- **Anomaly Detection**: Automatic detection of unusual patterns
- **Machine Learning**: Predictive analytics for system behavior
- **Alert System**: Configurable alerts for critical events
- **Export Capabilities**: Export reports in various formats (PDF, CSV)
- **Custom Dashboards**: User-configurable dashboard layouts