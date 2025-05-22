"""
Admin views for backup management.
Allows manual triggering of backups and viewing backup history.
"""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.contrib import messages
import os
import json
from datetime import datetime

from .tasks import (
    backup_postgres_database,
    backup_weaviate_database,
    backup_media_files,
    run_full_backup,
    BACKUP_PATHS
)

class BackupAdmin(admin.ModelAdmin):
    """
    Admin interface for backup management.
    Provides backup listing and manual triggering.
    """
    # This is a virtual model admin - doesn't have an actual model
    # but allows us to create a UI in Django admin
    
    # Minimal model fields for admin list
    list_display = ('backup_id', 'backup_type', 'created_at', 'size', 'status', 'actions')
    actions = None
    
    def get_urls(self):
        """Add custom URLs for backup actions."""
        urls = super().get_urls()
        custom_urls = [
            path('trigger-backup/', self.admin_site.admin_view(self.trigger_backup_view), name='trigger_backup'),
            path('trigger-backup/<str:backup_type>/', self.admin_site.admin_view(self.trigger_backup), name='trigger_backup_type'),
            path('restore-backup/<str:backup_id>/', self.admin_site.admin_view(self.restore_backup), name='restore_backup'),
        ]
        return custom_urls + urls
    
    def has_add_permission(self, request):
        """Disable add."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable edit."""
        return False
    
    def get_queryset(self, request):
        """Return an empty queryset since we're not using a real model."""
        return self.model.objects.none()
    
    def changelist_view(self, request, extra_context=None):
        """Override to display backup history."""
        # Get backup files
        backups = self.get_backup_list()
        
        # Add to context
        context = extra_context or {}
        context['backups'] = backups
        
        # Use custom template
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'admin/backup_list.html', context)
    
    def get_backup_list(self):
        """Get list of backups from disk."""
        backups = []
        
        for backup_type, backup_path in BACKUP_PATHS.items():
            if not os.path.exists(backup_path):
                continue
                
            for item in os.listdir(backup_path):
                item_path = os.path.join(backup_path, item)
                
                # Skip directories for postgres and media backups
                if backup_type != 'weaviate' and os.path.isdir(item_path):
                    continue
                    
                # Get file stats
                try:
                    stats = os.stat(item_path)
                    created_at = datetime.fromtimestamp(stats.st_ctime)
                    size_bytes = stats.st_size if os.path.isfile(item_path) else self._get_dir_size(item_path)
                    
                    backups.append({
                        'backup_id': item,
                        'backup_type': backup_type,
                        'created_at': created_at,
                        'path': item_path,
                        'size_bytes': size_bytes,
                        'size': self._format_size(size_bytes),
                        'status': 'completed'
                    })
                except Exception as e:
                    print(f"Error processing backup {item_path}: {e}")
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
    
    def _get_dir_size(self, path):
        """Get size of directory contents."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def _format_size(self, size_bytes):
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
    
    def backup_id(self, obj):
        """Display backup ID."""
        return obj.get('backup_id', 'Unknown')
    
    def backup_type(self, obj):
        """Display backup type."""
        return obj.get('backup_type', 'Unknown')
    
    def created_at(self, obj):
        """Display backup creation time."""
        created_at = obj.get('created_at')
        if created_at:
            return created_at.strftime('%Y-%m-%d %H:%M:%S')
        return 'Unknown'
    
    def size(self, obj):
        """Display backup size."""
        return obj.get('size', 'Unknown')
    
    def status(self, obj):
        """Display backup status."""
        return obj.get('status', 'Unknown')
    
    def actions(self, obj):
        """Display action buttons for backup."""
        backup_id = obj.get('backup_id', '')
        
        # Only show restore button for completed backups
        if obj.get('status') == 'completed':
            return format_html(
                '<a class="button" href="{}">Restore</a>',
                f'restore-backup/{backup_id}/'
            )
        return '-'
    
    def trigger_backup_view(self, request):
        """View for backup triggering page."""
        if request.method == 'POST':
            backup_type = request.POST.get('backup_type', 'all')
            return HttpResponseRedirect(f'trigger-backup/{backup_type}/')
        
        context = {
            'title': 'Trigger Backup',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/trigger_backup.html', context)
    
    def trigger_backup(self, request, backup_type):
        """Trigger a backup task."""
        try:
            if backup_type == 'postgres':
                result = backup_postgres_database.delay()
                messages.success(request, f'PostgreSQL backup triggered (Task ID: {result.id})')
            elif backup_type == 'weaviate':
                result = backup_weaviate_database.delay()
                messages.success(request, f'Weaviate backup triggered (Task ID: {result.id})')
            elif backup_type == 'media':
                result = backup_media_files.delay()
                messages.success(request, f'Media files backup triggered (Task ID: {result.id})')
            elif backup_type == 'all':
                result = run_full_backup.delay()
                messages.success(request, f'Full system backup triggered (Task ID: {result.id})')
            else:
                messages.error(request, f'Unknown backup type: {backup_type}')
        except Exception as e:
            messages.error(request, f'Error triggering backup: {str(e)}')
        
        return HttpResponseRedirect('../../')
    
    def restore_backup(self, request, backup_id):
        """View for backup restoration."""
        # This would be implemented to handle restore functionality
        # For now, just show an info message
        messages.info(request, f'Restore functionality for {backup_id} is not yet implemented')
        return HttpResponseRedirect('../../')


# Register our "virtual" model admin
admin.site.register(type('Backup', (object,), {'__module__': __name__}), BackupAdmin)