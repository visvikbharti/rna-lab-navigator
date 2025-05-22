"""
Signal handlers for authentication models.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserRole, UserPermission


@receiver(post_save, sender=User)
def create_default_user_role(sender, instance, created, **kwargs):
    """
    Assigns a default role to newly created users.
    New users get the 'guest' role by default.
    """
    if created:
        # Check if this is the first user (likely an admin/superuser)
        if User.objects.count() == 1:
            UserRole.objects.create(
                user=instance,
                role='admin',
                description='System administrator (first user)'
            )
        else:
            # Regular new users get 'guest' role
            UserRole.objects.create(
                user=instance,
                role='guest',
                description='Default role for new users'
            )