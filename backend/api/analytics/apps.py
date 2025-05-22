"""
Django app configuration for analytics.
"""

from django.apps import AppConfig
from django.conf import settings


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.analytics'
    label = 'api_analytics'  # Custom label to avoid any potential conflicts
    verbose_name = 'Analytics & Monitoring'
    
    def ready(self):
        """
        Initialize analytics app when Django starts.
        Start background monitoring if enabled.
        """
        try:
            # Import here to avoid circular imports
            from .monitor import start_background_monitoring
            
            # Start background monitoring if enabled
            if getattr(settings, 'ANALYTICS_MONITOR_SYSTEM', False):
                start_background_monitoring()
        except ImportError:
            # For demo purposes, we'll ignore this if monitor.py doesn't exist
            pass