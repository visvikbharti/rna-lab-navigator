"""
Application configuration for the security app.
"""

from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.security'
    label = 'api_security'  # Custom label to avoid any potential conflicts
    verbose_name = 'Security'
    
    def ready(self):
        # Import signal handlers if any
        pass