"""
Admin interface for security-related models and functionality.
"""

from django.contrib import admin
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html

from api.analytics.models import SecurityEvent


class SecurityAdminSite(admin.AdminSite):
    """Security-specific admin site."""
    site_header = "RNA Lab Navigator Security Administration"
    site_title = "Security Admin"
    index_title = "Security Dashboard"


# Create a custom security admin site
security_admin_site = SecurityAdminSite(name="security")


# Comment out the SecurityEvent admin registration to avoid conflicts with analytics app
# @admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Admin interface for security events."""
    
    list_display = ['event_type', 'timestamp', 'user_display', 'ip_address', 
                  'severity', 'description', 'is_resolved', 'actions']
    list_filter = ['event_type', 'severity', 'is_resolved', 'timestamp']
    search_fields = ['description', 'ip_address', 'user__username']
    readonly_fields = ['event_type', 'timestamp', 'user', 'ip_address', 
                     'description', 'severity', 'details']
    date_hierarchy = 'timestamp'
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return 'Anonymous'
    user_display.short_description = 'User'
    
    def actions(self, obj):
        """Generate action buttons for each event."""
        buttons = []
        
        # Add resolve button if not resolved
        if not obj.is_resolved:
            buttons.append(
                format_html(
                    '<a class="button" href="{}">Resolve</a>',
                    f'/admin/analytics/securityevent/{obj.pk}/resolve/'
                )
            )
        
        # Add block IP button for suspicious activity
        if obj.event_type in ['suspicious_activity', 'login_failure', 'access_denied']:
            if obj.ip_address:
                # Check if IP is already blocked
                is_blocked = cache.get(f"waf:ip_block:{obj.ip_address}", False)
                if not is_blocked:
                    buttons.append(
                        format_html(
                            '<a class="button" style="background-color: #aa0000; color: white;" href="{}">Block IP</a>',
                            f'/admin/analytics/securityevent/{obj.pk}/block-ip/'
                        )
                    )
                else:
                    buttons.append(
                        format_html(
                            '<a class="button" style="background-color: #00aa00; color: white;" href="{}">Unblock IP</a>',
                            f'/admin/analytics/securityevent/{obj.pk}/unblock-ip/'
                        )
                    )
        
        return format_html(' '.join(buttons))
    actions.short_description = 'Actions'
    
    def get_urls(self):
        """Add custom URLs for actions."""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/resolve/',
                self.admin_site.admin_view(self.resolve_view),
                name='securityevent-resolve',
            ),
            path(
                '<int:pk>/block-ip/',
                self.admin_site.admin_view(self.block_ip_view),
                name='securityevent-block-ip',
            ),
            path(
                '<int:pk>/unblock-ip/',
                self.admin_site.admin_view(self.unblock_ip_view),
                name='securityevent-unblock-ip',
            ),
            path(
                'blocked-ips/',
                self.admin_site.admin_view(self.blocked_ips_view),
                name='securityevent-blocked-ips',
            ),
            path(
                'unblock-ip-direct/',
                self.admin_site.admin_view(self.unblock_ip_direct_view),
                name='securityevent-unblock-ip-direct',
            ),
        ]
        return custom_urls + urls
    
    def resolve_view(self, request, pk):
        """View to resolve a security event."""
        event = SecurityEvent.objects.get(pk=pk)
        
        if request.method == 'POST':
            notes = request.POST.get('notes', '')
            event.resolve(request.user, notes)
            self.message_user(request, f"Security event {pk} resolved successfully.")
            return HttpResponseRedirect("../../")
        
        context = {
            **self.admin_site.each_context(request),
            'event': event,
            'title': f"Resolve Security Event: {event.description}",
        }
        return TemplateResponse(request, "admin/security/resolve_event.html", context)
    
    def block_ip_view(self, request, pk):
        """View to block an IP address."""
        event = SecurityEvent.objects.get(pk=pk)
        ip_address = event.ip_address
        
        if not ip_address:
            self.message_user(request, "No IP address to block.", level='error')
            return HttpResponseRedirect("../../")
        
        # Get block duration from settings (default: 24 hours)
        from django.conf import settings
        block_duration = getattr(settings, 'WAF_BLOCK_IP_DURATION', 86400)
        
        # Block the IP
        cache.set(f"waf:ip_block:{ip_address}", True, block_duration)
        
        # Log the action
        from api.analytics.collectors import AuditCollector
        AuditCollector.record_audit_event(
            event_type="security_setting",
            description=f"IP address {ip_address} manually blocked",
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            severity="warning",
            details={
                'blocked_ip': ip_address,
                'duration': block_duration,
                'related_event': pk,
            }
        )
        
        self.message_user(
            request, 
            f"IP address {ip_address} has been blocked for {block_duration // 3600} hours."
        )
        return HttpResponseRedirect("../../")
    
    def unblock_ip_view(self, request, pk):
        """View to unblock an IP address."""
        event = SecurityEvent.objects.get(pk=pk)
        ip_address = event.ip_address
        
        if not ip_address:
            self.message_user(request, "No IP address to unblock.", level='error')
            return HttpResponseRedirect("../../")
        
        # Unblock the IP
        cache.delete(f"waf:ip_block:{ip_address}")
        
        # Reset violation count
        cache.delete(f"waf:violation_count:{ip_address}")
        
        # Log the action
        from api.analytics.collectors import AuditCollector
        AuditCollector.record_audit_event(
            event_type="security_setting",
            description=f"IP address {ip_address} manually unblocked",
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            severity="info",
            details={
                'unblocked_ip': ip_address,
                'related_event': pk,
            }
        )
        
        self.message_user(
            request, 
            f"IP address {ip_address} has been unblocked."
        )
        return HttpResponseRedirect("../../")
    
    def unblock_ip_direct_view(self, request):
        """View to directly unblock an IP address from the blocked IPs page."""
        if request.method != 'POST':
            return HttpResponseRedirect("../blocked-ips/")
        
        ip_address = request.POST.get('ip_address')
        
        if not ip_address:
            self.message_user(request, "No IP address to unblock.", level='error')
            return HttpResponseRedirect("../blocked-ips/")
        
        # Unblock the IP
        cache.delete(f"waf:ip_block:{ip_address}")
        
        # Reset violation count
        cache.delete(f"waf:violation_count:{ip_address}")
        
        # Log the action
        from api.analytics.collectors import AuditCollector
        AuditCollector.record_audit_event(
            event_type="security_setting",
            description=f"IP address {ip_address} manually unblocked",
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            severity="info",
            details={
                'unblocked_ip': ip_address,
            }
        )
        
        self.message_user(
            request, 
            f"IP address {ip_address} has been unblocked."
        )
        return HttpResponseRedirect("../blocked-ips/")
    
    def blocked_ips_view(self, request):
        """View to list all blocked IPs."""
        # Get all WAF block keys from cache
        import re
        from django.core.cache import caches
        
        cache_client = caches['default'].client.get_client()
        
        # Get all keys matching the pattern
        blocked_ips = []
        pattern = "waf:ip_block:*"
        
        try:
            # This works for Redis cache backend
            for key in cache_client.scan_iter(pattern):
                key_str = key.decode('utf-8')
                ip = key_str.replace('waf:ip_block:', '')
                
                # Get TTL for the key
                ttl = cache_client.ttl(key)
                
                # Only include keys that are actually blocked (value is True)
                if cache.get(key_str):
                    blocked_ips.append({
                        'ip': ip,
                        'ttl': ttl,
                        'expires_in': f"{ttl // 3600}h {(ttl % 3600) // 60}m" if ttl > 0 else "Never",
                    })
        except (AttributeError, Exception) as e:
            # Fallback for other cache backends
            pass
        
        context = {
            **self.admin_site.each_context(request),
            'blocked_ips': blocked_ips,
            'title': "Blocked IP Addresses",
        }
        return TemplateResponse(request, "admin/security/blocked_ips.html", context)