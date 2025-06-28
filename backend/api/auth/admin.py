"""
Admin configuration for authentication models with GMP compliance.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with GMP compliance features."""
    
    # Display configuration
    list_display = (
        'username', 'employee_id', 'email', 'get_full_name', 
        'role', 'department', 'is_active', 'is_locked_display',
        'last_activity'
    )
    list_filter = (
        'role', 'is_active', 'is_staff', 'is_superuser',
        'department', 'data_access_agreement_signed',
        'date_joined', 'last_activity'
    )
    search_fields = (
        'username', 'first_name', 'last_name', 'email',
        'employee_id', 'department', 'designation'
    )
    ordering = ('-date_joined',)
    
    # Field grouping for edit form
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'email',
                'employee_id', 'department', 'designation', 'phone'
            )
        }),
        ('Permissions & Access', {
            'fields': (
                'role', 'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Security', {
            'fields': (
                'last_password_change', 'failed_login_attempts',
                'account_locked_until'
            ),
            'classes': ('collapse',)
        }),
        ('Compliance', {
            'fields': (
                'terms_accepted_at', 'data_access_agreement_signed',
                'training_completed'
            ),
            'classes': ('collapse',)
        }),
        ('Activity Tracking', {
            'fields': (
                'last_login', 'last_activity', 'total_queries',
                'total_documents_uploaded'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'date_joined', 'created_by', 'notes',
                'notification_preferences'
            ),
            'classes': ('collapse',)
        }),
    )
    
    # Fields for creating new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2',
                'email', 'first_name', 'last_name',
                'employee_id', 'role', 'department'
            ),
        }),
    )
    
    # Read-only fields
    readonly_fields = (
        'last_login', 'date_joined', 'last_activity',
        'last_password_change', 'total_queries',
        'total_documents_uploaded'
    )
    
    def is_locked_display(self, obj):
        """Display lock status with color coding."""
        if obj.is_locked:
            return format_html(
                '<span style="color: red;">🔒 Locked</span>'
            )
        return format_html(
            '<span style="color: green;">✓ Active</span>'
        )
    is_locked_display.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('created_by')
    
    def save_model(self, request, obj, form, change):
        """Track who created/modified users."""
        if not change:  # Creating new user
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            user_role=request.user.role,
            action='USER_UPDATED' if change else 'USER_CREATED',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            resource=f"User: {obj.username}",
            details={
                'target_user_id': obj.id,
                'target_username': obj.username,
                'changes': list(form.changed_data) if change else 'New user created'
            }
        )
    
    def get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    # Custom actions
    actions = ['unlock_users', 'reset_failed_attempts', 'export_user_list']
    
    def unlock_users(self, request, queryset):
        """Unlock selected users."""
        count = 0
        for user in queryset:
            if user.is_locked:
                user.account_locked_until = None
                user.failed_login_attempts = 0
                user.save()
                count += 1
                
                # Log the action
                AuditLog.objects.create(
                    user=request.user,
                    username=request.user.username,
                    user_role=request.user.role,
                    action='ACCOUNT_UNLOCKED',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    resource=f"User: {user.username}",
                    details={'unlocked_by': request.user.username}
                )
        
        self.message_user(request, f"{count} users unlocked successfully.")
    unlock_users.short_description = "Unlock selected users"
    
    def reset_failed_attempts(self, request, queryset):
        """Reset failed login attempts."""
        count = queryset.update(failed_login_attempts=0)
        self.message_user(request, f"Reset failed attempts for {count} users.")
    reset_failed_attempts.short_description = "Reset failed login attempts"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs - read-only for compliance."""
    
    list_display = (
        'timestamp', 'username', 'user_role', 'action',
        'resource', 'ip_address', 'success_display'
    )
    list_filter = (
        'action', 'success', 'user_role',
        'timestamp',
    )
    search_fields = (
        'username', 'ip_address', 'resource',
        'user_agent', 'session_id'
    )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    # Make all fields read-only for compliance
    readonly_fields = [field.name for field in AuditLog._meta.fields]
    
    def success_display(self, obj):
        """Display success status with icons."""
        if obj.success:
            return format_html(
                '<span style="color: green;">✓</span>'
            )
        return format_html(
            '<span style="color: red;">✗</span>'
        )
    success_display.short_description = 'Success'
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs for compliance."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification of audit logs."""
        return False
    
    def get_actions(self, request):
        """Remove all actions for audit logs."""
        actions = super().get_actions(request)
        actions.clear()
        return actions