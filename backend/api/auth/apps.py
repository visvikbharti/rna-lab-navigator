"""
Application configuration for the auth app.
"""

from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.auth'
    label = 'api_auth'  # Custom label to avoid conflict with django.contrib.auth
    verbose_name = 'Authentication'
    
    def ready(self):
        # Signal handlers can be imported here if needed
        pass