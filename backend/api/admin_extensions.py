"""
Admin site extensions for registering custom admin views.
"""

from django.urls import path
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class AdminSite(admin.AdminSite):
    """Extended admin site with support for custom views"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry_custom = {}
    
    def register_view(self, path, view, name=None, category=None, icon_name=None):
        """
        Register a custom view with the admin site.
        
        Args:
            path: URL path for the view
            view: View function or class
            name: Display name for the view
            category: Admin category for the view
            icon_name: Icon name for the view
        """
        self._registry_custom[path] = {
            'view': view,
            'name': name or path,
            'category': category,
            'icon_name': icon_name,
        }
    
    def get_urls(self):
        """Get URLs for the admin site, including custom views"""
        urls = super().get_urls()
        
        # Add custom view URLs
        custom_urls = []
        for path, config in self._registry_custom.items():
            custom_urls.append(
                path(path, config['view'], name=path.replace('/', '_'))
            )
        
        return custom_urls + urls


# Extension for admin.site to support registering custom views
def register_view(path, name=None, category=None, icon_name=None):
    """
    Decorator to register a class-based view with the admin site.
    
    Args:
        path: URL path for the view
        name: Display name for the view
        category: Admin category for the view
        icon_name: Icon name for the view
    """
    def decorator(view_class):
        admin.site.register_view(path, view_class, name, category, icon_name)
        return view_class
    return decorator