"""
Admin views for LLM network isolation management.
"""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.contrib import messages
from django.urls import path
from django.conf import settings
import json
import os

from .isolation import (
    check_isolation_status,
    get_recommended_isolation_settings
)


class LLMIsolationAdmin(admin.ModelAdmin):
    """Admin panel for LLM network isolation management."""
    
    # This is a virtual model admin - doesn't have an actual model
    # but allows us to create a UI in Django admin
    
    actions = None
    
    def get_urls(self):
        """Add custom URLs for isolation management."""
        urls = super().get_urls()
        custom_urls = [
            path('isolation-status/', self.admin_site.admin_view(self.isolation_status_view), name='llm_isolation_status'),
            path('toggle-isolation/', self.admin_site.admin_view(self.toggle_isolation_view), name='toggle_llm_isolation'),
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
        """Override to display isolation status."""
        # Redirect to isolation status view
        return HttpResponseRedirect('isolation-status/')
    
    def isolation_status_view(self, request):
        """View for displaying LLM isolation status."""
        # Get isolation status
        status = check_isolation_status()
        
        # Get current settings
        current_settings = {
            'LLM_NETWORK_ISOLATION': getattr(settings, 'LLM_NETWORK_ISOLATION', False),
            'LLM_FORCE_ISOLATION': getattr(settings, 'LLM_FORCE_ISOLATION', False),
            'OLLAMA_API_URL': getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434'),
            'OLLAMA_DEFAULT_MODEL': getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'Unknown'),
            'LOCAL_EMBEDDING_MODEL_PATH': getattr(settings, 'LOCAL_EMBEDDING_MODEL_PATH', 'Not configured'),
            'LOCAL_EMBEDDING_TOKENIZER_PATH': getattr(settings, 'LOCAL_EMBEDDING_TOKENIZER_PATH', 'Not configured'),
            'ENV_FILE_PATH': os.path.join(settings.BASE_DIR, '.env'),
        }
        
        # Get recommended settings
        recommendations = get_recommended_isolation_settings()
        
        context = {
            'title': 'LLM Network Isolation Status',
            'status': status,
            'current_settings': current_settings,
            'recommendations': recommendations,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'admin/llm_isolation_status.html', context)
    
    def toggle_isolation_view(self, request):
        """View for toggling isolation mode."""
        if request.method != 'POST':
            return HttpResponseRedirect('../isolation-status/')
        
        # Get current isolation setting
        current_isolation = getattr(settings, 'LLM_NETWORK_ISOLATION', False)
        
        # This is a simplified version since we can't actually modify settings.py or .env at runtime
        # In a real implementation, this would update the .env file or database settings
        
        if current_isolation:
            messages.success(request, 'LLM network isolation would be disabled. In a real implementation, this would update your .env file.')
        else:
            # Check if local LLM is available
            status = check_isolation_status()
            if not status['local_available']:
                messages.error(request, 'Cannot enable isolation: local LLM is not available. Please install and configure a local LLM first.')
                return HttpResponseRedirect('../isolation-status/')
            
            messages.success(request, 'LLM network isolation would be enabled. In a real implementation, this would update your .env file.')
        
        return HttpResponseRedirect('../isolation-status/')


# Register our "virtual" model admin
admin.site.register(type('LLMIsolation', (object,), {'__module__': __name__}), LLMIsolationAdmin)