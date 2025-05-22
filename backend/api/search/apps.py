"""
Application configuration for the search app.
"""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.search'
    label = 'api_search'  # Custom label to avoid any potential conflicts
    verbose_name = 'Enhanced Search'
    
    def ready(self):
        # Import signal handlers if any
        pass