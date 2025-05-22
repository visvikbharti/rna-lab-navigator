"""
Views for security audit and monitoring dashboard.
Provides API endpoints for security metrics, alerts, and administration.
"""

from django.db.models import Count, F, Q, Sum, Avg, Max, Min
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from datetime import datetime, timedelta
import logging

from api.analytics.models import SecurityEvent, AuditEvent
from .models import BlockedIP, SecurityConfiguration, SecurityScan, SecurityIncident, WAFAlert
from .serializers import (
    SecurityEventSerializer, 
    BlockedIPSerializer,
    SecurityIncidentSerializer,
    SecurityConfigurationSerializer,
    WAFAlertSerializer,
    SecurityScanSerializer
)

logger = logging.getLogger(__name__)


class SecurityEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for security events."""
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = SecurityEvent.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type', None)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by severity
        severity = self.request.query_params.get('severity', None)
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by resolution status
        is_resolved = self.request.query_params.get('is_resolved', None)
        if is_resolved is not None:
            is_resolved = is_resolved.lower() == 'true'
            queryset = queryset.filter(is_resolved=is_resolved)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get a summary of security events."""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Aggregate events by time period
        events_24h = SecurityEvent.objects.filter(timestamp__gte=last_24h).count()
        events_7d = SecurityEvent.objects.filter(timestamp__gte=last_7d).count()
        events_30d = SecurityEvent.objects.filter(timestamp__gte=last_30d).count()
        
        # Aggregate events by severity
        critical = SecurityEvent.objects.filter(severity='critical').count()
        error = SecurityEvent.objects.filter(severity='error').count()
        warning = SecurityEvent.objects.filter(severity='warning').count()
        info = SecurityEvent.objects.filter(severity='info').count()
        
        # Aggregate events by type
        event_types = SecurityEvent.objects.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Aggregate resolved vs unresolved
        resolved = SecurityEvent.objects.filter(is_resolved=True).count()
        unresolved = SecurityEvent.objects.filter(is_resolved=False).count()
        
        return Response({
            'time_periods': {
                'last_24h': events_24h,
                'last_7d': events_7d,
                'last_30d': events_30d,
                'total': SecurityEvent.objects.count(),
            },
            'by_severity': {
                'critical': critical,
                'error': error,
                'warning': warning,
                'info': info,
            },
            'by_type': list(event_types),
            'resolution_status': {
                'resolved': resolved,
                'unresolved': unresolved,
            }
        })
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trends of security events over time."""
        now = timezone.now()
        days = int(request.query_params.get('days', 30))
        start_date = now - timedelta(days=days)
        
        # Get daily counts
        daily_events = SecurityEvent.objects.filter(
            timestamp__gte=start_date
        ).values(
            date=F('timestamp__date')
        ).annotate(
            count=Count('id'),
            critical=Count('id', filter=Q(severity='critical')),
            error=Count('id', filter=Q(severity='error')),
            warning=Count('id', filter=Q(severity='warning')),
            info=Count('id', filter=Q(severity='info')),
        ).order_by('date')
        
        return Response(list(daily_events))
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark a security event as resolved."""
        event = self.get_object()
        notes = request.data.get('notes', '')
        
        if event.is_resolved:
            return Response({
                'error': 'Event is already resolved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event.resolve(request.user, notes)
            return Response({
                'status': 'success',
                'message': 'Event marked as resolved'
            })
        except Exception as e:
            logger.error(f"Error resolving security event: {e}")
            return Response({
                'error': 'Failed to resolve event'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlockedIPViewSet(viewsets.ModelViewSet):
    """ViewSet for blocked IP addresses."""
    queryset = BlockedIP.objects.all()
    serializer_class = BlockedIPSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """Unblock an IP address."""
        blocked_ip = self.get_object()
        
        try:
            # If permanent, delete the record; otherwise update blocked_until
            if blocked_ip.is_permanent:
                blocked_ip.delete()
                message = f"IP {blocked_ip.ip_address} has been permanently unblocked"
            else:
                blocked_ip.blocked_until = timezone.now()
                blocked_ip.save()
                message = f"IP {blocked_ip.ip_address} has been unblocked"
            
            # Log the unblock action
            AuditEvent.objects.create(
                event_type='security_setting',
                user=request.user,
                description=f"Unblocked IP: {blocked_ip.ip_address}",
                severity='info',
                details={
                    'ip_address': blocked_ip.ip_address,
                    'reason': blocked_ip.reason,
                    'was_permanent': blocked_ip.is_permanent,
                }
            )
            
            return Response({
                'status': 'success',
                'message': message
            })
        except Exception as e:
            logger.error(f"Error unblocking IP: {e}")
            return Response({
                'error': 'Failed to unblock IP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def block(self, request):
        """Block an IP address."""
        ip_address = request.data.get('ip_address')
        reason = request.data.get('reason', 'manual')
        is_permanent = request.data.get('is_permanent', True)
        description = request.data.get('description', '')
        duration_hours = request.data.get('duration_hours', 24)
        
        if not ip_address:
            return Response({
                'error': 'IP address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        blocked_until = None
        if not is_permanent:
            blocked_until = timezone.now() + timedelta(hours=duration_hours)
        
        try:
            # Check if IP is already blocked
            if BlockedIP.objects.filter(ip_address=ip_address).exists():
                # Update existing record
                blocked_ip = BlockedIP.objects.get(ip_address=ip_address)
                blocked_ip.reason = reason
                blocked_ip.is_permanent = is_permanent
                blocked_ip.blocked_until = blocked_until
                blocked_ip.description = description
                blocked_ip.blocked_by = request.user
                blocked_ip.blocked_at = timezone.now()
                blocked_ip.save()
                message = f"Updated block for IP {ip_address}"
            else:
                # Create new block
                blocked_ip = BlockedIP.objects.create(
                    ip_address=ip_address,
                    reason=reason,
                    is_permanent=is_permanent,
                    blocked_until=blocked_until,
                    description=description,
                    blocked_by=request.user
                )
                message = f"IP {ip_address} has been blocked"
            
            # Log the block action
            AuditEvent.objects.create(
                event_type='security_setting',
                user=request.user,
                description=f"Blocked IP: {ip_address}",
                severity='warning',
                details={
                    'ip_address': ip_address,
                    'reason': reason,
                    'is_permanent': is_permanent,
                    'duration_hours': duration_hours if not is_permanent else None,
                }
            )
            
            return Response({
                'status': 'success',
                'message': message,
                'blocked_ip': BlockedIPSerializer(blocked_ip).data
            })
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
            return Response({
                'error': 'Failed to block IP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SecurityIncidentViewSet(viewsets.ModelViewSet):
    """ViewSet for security incidents."""
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status of a security incident."""
        incident = self.get_object()
        status = request.data.get('status')
        
        valid_statuses = [s[0] for s in SecurityIncident.STATUS_CHOICES]
        if not status or status not in valid_statuses:
            return Response({
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            incident.status = status
            
            # If status is 'resolved' or 'closed', record resolution info
            if status in ['resolved', 'closed']:
                incident.resolved_at = timezone.now()
                incident.resolved_by = request.user
                
                # Update resolution fields if provided
                if 'response_actions' in request.data:
                    incident.response_actions = request.data['response_actions']
                if 'root_cause_analysis' in request.data:
                    incident.root_cause_analysis = request.data['root_cause_analysis']
                if 'prevention_measures' in request.data:
                    incident.prevention_measures = request.data['prevention_measures']
            
            incident.save()
            
            return Response({
                'status': 'success',
                'message': f'Incident status updated to {status}'
            })
        except Exception as e:
            logger.error(f"Error updating incident status: {e}")
            return Response({
                'error': 'Failed to update incident status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WAFAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for WAF alerts."""
    queryset = WAFAlert.objects.all()
    serializer_class = WAFAlertSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = WAFAlert.objects.all()
        
        # Filter by attack type
        attack_type = self.request.query_params.get('attack_type', None)
        if attack_type:
            queryset = queryset.filter(attack_type=attack_type)
        
        # Filter by severity
        severity = self.request.query_params.get('severity', None)
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by action taken
        action_taken = self.request.query_params.get('action_taken', None)
        if action_taken:
            queryset = queryset.filter(action_taken=action_taken)
        
        # Filter by false positive
        false_positive = self.request.query_params.get('false_positive', None)
        if false_positive is not None:
            false_positive = false_positive.lower() == 'true'
            queryset = queryset.filter(is_false_positive=false_positive)
        
        # Filter by IP address
        ip_address = self.request.query_params.get('ip_address', None)
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_false_positive(self, request, pk=None):
        """Mark a WAF alert as a false positive."""
        alert = self.get_object()
        notes = request.data.get('notes', '')
        
        try:
            alert.is_false_positive = True
            alert.notes = notes
            alert.save()
            
            return Response({
                'status': 'success',
                'message': 'Alert marked as false positive'
            })
        except Exception as e:
            logger.error(f"Error marking WAF alert as false positive: {e}")
            return Response({
                'error': 'Failed to update alert'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
@cache_page(60 * 5)  # Cache for 5 minutes
def security_dashboard_summary(request):
    """Get a summary of security metrics for the dashboard."""
    # Time intervals
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    try:
        # Collect security metrics
        security_metrics = {
            'total_incidents': SecurityIncident.objects.count(),
            'open_incidents': SecurityIncident.objects.exclude(status__in=['resolved', 'closed']).count(),
            'critical_incidents': SecurityIncident.objects.filter(severity='critical').count(),
            'waf_alerts_24h': WAFAlert.objects.filter(timestamp__gte=last_24h).count(),
            'security_events_24h': SecurityEvent.objects.filter(timestamp__gte=last_24h).count(),
            'blocked_ips': BlockedIP.objects.filter(
                Q(is_permanent=True) | Q(blocked_until__gt=now)
            ).count(),
            'failed_logins_24h': SecurityEvent.objects.filter(
                event_type='login_failure',
                timestamp__gte=last_24h
            ).count(),
            'suspicious_activities_24h': SecurityEvent.objects.filter(
                event_type='suspicious_activity',
                timestamp__gte=last_24h
            ).count(),
        }
        
        # Top attack vectors (last 7 days)
        top_attack_vectors = WAFAlert.objects.filter(
            timestamp__gte=last_7d
        ).values('attack_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Top targeted endpoints (last 7 days)
        top_targeted_endpoints = WAFAlert.objects.filter(
            timestamp__gte=last_7d
        ).values('request_path').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Recent security incidents
        recent_incidents = SecurityIncidentSerializer(
            SecurityIncident.objects.all()[:5],
            many=True
        ).data
        
        # Daily security events (last 30 days)
        daily_events = SecurityEvent.objects.filter(
            timestamp__gte=last_30d
        ).values(
            date=F('timestamp__date')
        ).annotate(
            count=Count('id')
        ).order_by('date')
        
        # Aggregate WAF alerts by attack type
        waf_by_attack_type = WAFAlert.objects.values('attack_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Aggregate security events by type
        events_by_type = SecurityEvent.objects.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'metrics': security_metrics,
            'top_attack_vectors': list(top_attack_vectors),
            'top_targeted_endpoints': list(top_targeted_endpoints),
            'recent_incidents': recent_incidents,
            'daily_events': list(daily_events),
            'waf_by_attack_type': list(waf_by_attack_type),
            'events_by_type': list(events_by_type),
        })
    except Exception as e:
        logger.error(f"Error generating security dashboard summary: {e}")
        return Response({
            'error': 'Failed to generate security dashboard summary'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def security_health_check(request):
    """Perform a security health check and return findings."""
    findings = []
    
    # Check for unresolved critical security incidents
    critical_incidents = SecurityIncident.objects.filter(
        severity='critical',
        status__in=['detected', 'investigating']
    ).count()
    if critical_incidents > 0:
        findings.append({
            'severity': 'critical',
            'message': f'There are {critical_incidents} unresolved critical security incidents',
            'recommendation': 'Review and address critical security incidents immediately',
        })
    
    # Check for recent brute force attempts
    recent_brute_force = SecurityEvent.objects.filter(
        event_type='login_failure',
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).count()
    if recent_brute_force > 10:
        findings.append({
            'severity': 'high',
            'message': f'High number of login failures detected: {recent_brute_force} in the last 24 hours',
            'recommendation': 'Review login security measures and monitor for account takeover attempts',
        })
    
    # Check for WAF bypass attempts
    waf_bypasses = WAFAlert.objects.filter(
        severity__in=['critical', 'high'],
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).count()
    if waf_bypasses > 5:
        findings.append({
            'severity': 'high',
            'message': f'Detected {waf_bypasses} high or critical WAF alerts in the past week',
            'recommendation': 'Review WAF rules and enhance protection for targeted endpoints',
        })
    
    # Check for security configuration changes
    recent_config_changes = SecurityConfiguration.objects.filter(
        changed_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    if recent_config_changes > 0:
        findings.append({
            'severity': 'medium',
            'message': f'There have been {recent_config_changes} security configuration changes in the past week',
            'recommendation': 'Review recent security configuration changes for compliance',
        })
    
    # Check for outdated security scans
    latest_scan = SecurityScan.objects.filter(
        status='completed'
    ).order_by('-completed_at').first()
    if not latest_scan or (latest_scan.completed_at and latest_scan.completed_at < timezone.now() - timedelta(days=30)):
        findings.append({
            'severity': 'medium',
            'message': 'No security scan has been completed in the past 30 days',
            'recommendation': 'Schedule a vulnerability scan to identify potential security issues',
        })
    
    # Overall health status
    critical_count = sum(1 for f in findings if f['severity'] == 'critical')
    high_count = sum(1 for f in findings if f['severity'] == 'high')
    
    if critical_count > 0:
        health_status = 'critical'
    elif high_count > 0:
        health_status = 'at_risk'
    elif findings:
        health_status = 'warning'
    else:
        health_status = 'healthy'
    
    return Response({
        'status': health_status,
        'findings': findings,
        'last_checked': timezone.now().isoformat(),
        'checks_performed': 5,
        'critical_issues': critical_count,
        'high_issues': high_count,
        'medium_issues': len(findings) - critical_count - high_count,
    })