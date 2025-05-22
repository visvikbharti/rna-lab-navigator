"""
Application configuration for the feedback app.
"""

from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.feedback'
    label = 'api_feedback'  # Custom label to avoid any potential conflicts
    verbose_name = 'User Feedback'
    
    def ready(self):
        # Import signal handlers if any
        pass