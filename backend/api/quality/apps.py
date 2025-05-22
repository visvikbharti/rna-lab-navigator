"""
Application configuration for the quality app.
"""

from django.apps import AppConfig


class QualityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.quality'
    label = 'api_quality'  # Custom label to avoid any potential conflicts
    verbose_name = 'Quality Improvement'
    
    def ready(self):
        # Import signal handlers if any
        pass