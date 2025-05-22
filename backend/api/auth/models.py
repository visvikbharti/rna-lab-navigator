"""
Authentication models for the RNA Lab Navigator.
Provides models for user roles and permissions management.
"""

from django.db import models
from django.contrib.auth.models import User


class UserRole(models.Model):
    """
    Defines user roles for role-based access control (RBAC).
    Each user can have one or more roles.
    """
    
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Lab Manager'),
        ('researcher', 'Researcher'),
        ('assistant', 'Lab Assistant'),
        ('student', 'Student'),
        ('guest', 'Guest'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    description = models.TextField(blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='created_roles')
    
    class Meta:
        unique_together = ['user', 'role']
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class UserPermission(models.Model):
    """
    Defines user-specific permissions.
    These are additional permissions beyond roles.
    """
    
    PERMISSION_CHOICES = (
        ('can_upload', 'Can Upload Documents'),
        ('can_delete', 'Can Delete Documents'),
        ('can_modify', 'Can Modify Documents'),
        ('can_export', 'Can Export Data'),
        ('can_share', 'Can Share Documents'),
        ('can_create_users', 'Can Create Users'),
        ('can_manage_users', 'Can Manage Users'),
        ('can_manage_roles', 'Can Manage Roles'),
        ('can_view_analytics', 'Can View Analytics'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions')
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='granted_permissions')
    
    class Meta:
        unique_together = ['user', 'permission']
        verbose_name = 'User Permission'
        verbose_name_plural = 'User Permissions'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_permission_display()}"


class AccessAttempt(models.Model):
    """
    Records failed access attempts for security monitoring.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    path = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Access Attempt'
        verbose_name_plural = 'Access Attempts'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.username or 'Unknown'} - {self.ip_address} - {'Success' if self.is_successful else 'Failure'}"