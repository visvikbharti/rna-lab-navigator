import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")

app = Celery("rna_backend")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Set up the celery beat schedule
app.conf.beat_schedule = {
    # Fetch new bioRxiv papers at 2 AM daily (respecting CELERY_TIMEZONE="Asia/Kolkata" in settings)
    'fetch-biorxiv-papers-daily': {
        'task': 'fetch_biorxiv_preprints',
        'schedule': crontab(hour=2, minute=0),
    },
    # Run system evaluation weekly (Sunday 3 AM)
    'run-weekly-evaluation': {
        'task': 'run_weekly_evaluation',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
    },
    # Clean up old cache entries weekly (Saturday 1 AM)
    'cleanup-old-cache-entries': {
        'task': 'cleanup_old_cache_entries',
        'schedule': crontab(day_of_week=6, hour=1, minute=0),
    },
    
    # Analytics tasks
    # Daily metrics aggregation (1 AM)
    'aggregate-daily-metrics': {
        'task': 'api.analytics.tasks.aggregate_daily_metrics',
        'schedule': crontab(hour=1, minute=0),
    },
    # Weekly analytics report (Monday 1:30 AM)
    'generate-weekly-report': {
        'task': 'api.analytics.tasks.generate_weekly_report',
        'schedule': crontab(day_of_week=1, hour=1, minute=30),
    },
    # System performance monitoring (every 15 minutes)
    'monitor-system-performance': {
        'task': 'api.analytics.tasks.monitor_system_performance',
        'schedule': crontab(minute='*/15'),
    },
    # Clean up old metrics (first day of month, 2 AM)
    'cleanup-old-metrics': {
        'task': 'api.analytics.tasks.cleanup_old_metrics',
        'schedule': crontab(day_of_month=1, hour=2, minute=0),
        'kwargs': {'days_to_keep': 90},
    },
    
    # Quality improvement tasks
    # Weekly quality analysis (Tuesday 2 AM)
    'weekly-quality-analysis': {
        'task': 'api.quality.tasks.run_quality_analysis',
        'schedule': crontab(day_of_week=2, hour=2, minute=0),
        'kwargs': {'days': 30},
    },
    # Generate quality recommendations (Tuesday 2:30 AM)
    'generate-quality-recommendations': {
        'task': 'api.quality.tasks.generate_improvement_recommendations',
        'schedule': crontab(day_of_week=2, hour=2, minute=30),
    },
    # Auto-approve high-priority improvements (Tuesday 3 AM)
    'auto-approve-improvements': {
        'task': 'api.quality.tasks.auto_approve_improvements',
        'schedule': crontab(day_of_week=2, hour=3, minute=0),
        'kwargs': {'priority_level': 'high', 'max_count': 3},
    },
    # Implement approved improvements (Sunday 2 AM)
    'implement-improvements': {
        'task': 'api.quality.tasks.implement_improvements',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
        'kwargs': {'execute': True},
    },
    # Run full quality pipeline bi-weekly (1st and 15th of month, 1 AM)
    'run-quality-pipeline': {
        'task': 'api.quality.tasks.run_quality_pipeline',
        'schedule': crontab(day_of_month='1,15', hour=1, minute=0),
        'kwargs': {'auto_approve': True, 'auto_implement': False},
    },
    
    # Backup tasks
    # Daily Postgres database backup (2 AM)
    'daily-postgres-backup': {
        'task': 'api.backup.tasks.backup_postgres_database',
        'schedule': crontab(hour=2, minute=0),
    },
    # Daily Weaviate vector database backup (3 AM)
    'daily-weaviate-backup': {
        'task': 'api.backup.tasks.backup_weaviate_database',
        'schedule': crontab(hour=3, minute=0),
    },
    # Daily media files backup (4 AM)
    'daily-media-backup': {
        'task': 'api.backup.tasks.backup_media_files',
        'schedule': crontab(hour=4, minute=0),
    },
    # Weekly full system backup (Sunday 1 AM)
    'weekly-full-backup': {
        'task': 'api.backup.tasks.run_full_backup',
        'schedule': crontab(day_of_week=0, hour=1, minute=0),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')