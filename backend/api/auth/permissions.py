"""
Custom permission classes for the RNA Lab Navigator.
Provides permission classes for role-based access control (RBAC).
"""

from rest_framework import permissions
from .models import UserRole, UserPermission


class IsAdmin(permissions.BasePermission):
    """
    Permission class that checks if the user has admin role.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super users have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user has admin role
        return UserRole.objects.filter(user=request.user, role='admin').exists()


class IsLabManager(permissions.BasePermission):
    """
    Permission class that checks if the user has lab manager role.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super users and admins have all permissions
        if request.user.is_superuser:
            return True
        
        if UserRole.objects.filter(user=request.user, role='admin').exists():
            return True
        
        # Check if user has lab manager role
        return UserRole.objects.filter(user=request.user, role='manager').exists()


class IsResearcher(permissions.BasePermission):
    """
    Permission class that checks if the user has researcher role.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super users, admins, and lab managers have all permissions
        if request.user.is_superuser:
            return True
        
        if UserRole.objects.filter(user=request.user, role__in=['admin', 'manager']).exists():
            return True
        
        # Check if user has researcher role
        return UserRole.objects.filter(user=request.user, role='researcher').exists()


class HasRolePermission(permissions.BasePermission):
    """
    Permission class that checks if the user has one of the specified roles.
    """
    
    def __init__(self, allowed_roles=None):
        self.allowed_roles = allowed_roles or ['admin', 'manager', 'researcher']
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super users have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user has any of the allowed roles
        return UserRole.objects.filter(user=request.user, role__in=self.allowed_roles).exists()


class HasSpecificPermission(permissions.BasePermission):
    """
    Permission class that checks if the user has a specific permission.
    """
    
    def __init__(self, required_permission=None):
        self.required_permission = required_permission
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super users have all permissions
        if request.user.is_superuser:
            return True
        
        # Admins have all permissions
        if UserRole.objects.filter(user=request.user, role='admin').exists():
            return True
        
        # Check if user has required permission
        if not self.required_permission:
            return False
        
        return UserPermission.objects.filter(
            user=request.user, 
            permission=self.required_permission
        ).exists()


# Common permission compositions
class CanUploadDocuments(HasSpecificPermission):
    def __init__(self):
        super().__init__(required_permission='can_upload')


class CanDeleteDocuments(HasSpecificPermission):
    def __init__(self):
        super().__init__(required_permission='can_delete')


class CanModifyDocuments(HasSpecificPermission):
    def __init__(self):
        super().__init__(required_permission='can_modify')


class CanViewAnalytics(HasSpecificPermission):
    def __init__(self):
        super().__init__(required_permission='can_view_analytics')


class CanManageUsers(HasSpecificPermission):
    def __init__(self):
        super().__init__(required_permission='can_manage_users')