"""
Admin configuration for authentication models.
"""

from django.contrib import admin
from .models import UserRole, UserPermission, AccessAttempt


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at', 'created_by')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'role')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'created_by')


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission', 'created_at', 'granted_by')
    list_filter = ('permission', 'created_at')
    search_fields = ('user__username', 'user__email', 'permission')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'granted_by')


@admin.register(AccessAttempt)
class AccessAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'path', 'timestamp', 'is_successful')
    list_filter = ('is_successful', 'timestamp')
    search_fields = ('username', 'ip_address', 'path', 'user_agent')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('user',)
    readonly_fields = ('user', 'username', 'ip_address', 'user_agent', 'path', 'timestamp', 'is_successful')