# Backup System for RNA Lab Navigator

This module provides automated backup and restoration capabilities for RNA Lab Navigator, ensuring data safety and disaster recovery.

## Overview

The backup system handles three critical data components:

1. **PostgreSQL Database**: Contains user data, search history, analytics, and more
2. **Weaviate Vector Database**: Stores document embeddings for RAG-based Q&A
3. **Media Files**: Includes extracted figures, uploaded documents, and other multimedia content

## Features

- Automated scheduled backups (daily and weekly)
- Manual backup triggering via Django Admin
- Multi-destination backup storage (local filesystem and S3-compatible storage)
- Backup rotation with configurable retention period
- Restoration capabilities for disaster recovery

## Configuration

Backup settings are configured in `settings.py` and can be overridden with environment variables:

```
# Backup settings
BACKUP_RETENTION_DAYS=7               # Number of days to keep backups
BACKUP_CLEANUP_LOCAL=False            # Remove local backups after S3 upload
AWS_BACKUP_BUCKET=your-bucket-name    # S3 bucket for backups (optional)
AWS_ACCESS_KEY_ID=your-access-key     # S3 access key (optional)
AWS_SECRET_ACCESS_KEY=your-secret-key # S3 secret key (optional)
AWS_S3_ENDPOINT=https://s3.amazonaws.com # S3 endpoint URL (optional)
```

## Schedule

By default, backups are scheduled as follows:

- **PostgreSQL Database**: Daily at 2:00 AM
- **Weaviate Vector Database**: Daily at 3:00 AM
- **Media Files**: Daily at 4:00 AM
- **Complete Backup**: Weekly on Sunday at 1:00 AM

Schedule can be modified in `rna_backend/celery.py`.

## Usage

### Automatic Backups

Backups run automatically according to the schedule defined in Celery Beat. No user action is required.

### Manual Backups

Administrators can trigger manual backups through the Django Admin interface:

1. Navigate to Django Admin > Backup Management
2. Click "Trigger Backup"
3. Select the backup type (Full System, PostgreSQL, Weaviate, or Media)
4. Click "Trigger Backup" to start the process

### Backup Storage

Backups are stored in the following locations:

- **Local**: `<project_root>/backend/backups/<component>/`
- **S3**: `<bucket_name>/<component>/<backup_name>`

### Restoration

Restoration can be initiated from the Django Admin interface:

1. Navigate to Django Admin > Backup Management
2. Find the backup you want to restore
3. Click "Restore" next to the backup

**Warning**: Restoration will overwrite existing data. Use with caution.

## Implementation Details

- Backups are managed by Celery tasks in `tasks.py`
- PostgreSQL backups use `pg_dump` with the custom format
- Weaviate backups use the Weaviate Backup API
- Media backups are packaged as compressed tar archives
- Restoration functions are in `restore.py`

## Monitoring

Backup progress and status can be monitored through:

- Celery logs
- Django Admin > Backup Management
- System logs (when running in production mode)

## Troubleshooting

If backups are failing, check:

1. Disk space availability
2. Database connection settings
3. S3 credentials (if using S3 storage)
4. Log files for detailed error messages

For restoration failures:

1. Ensure the backup file exists and is accessible
2. Verify database connection settings
3. Check permissions on media directories
4. Review logs for detailed error messages