"""
Admin views for user management with GMP compliance.
"""

from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta

from .models import User, AuditLog
from .serializers import UserSerializer, AuditLogSerializer
from .utils import get_client_ip, is_password_complex
from .permissions import IsAdminOrPI


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management operations.
    Only accessible by Admins and PIs.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrPI]
    
    def get_queryset(self):
        """Filter and annotate queryset with additional info."""
        queryset = super().get_queryset()
        
        # Add annotations for admin dashboard
        queryset = queryset.annotate(
            audit_count=Count('audit_logs', distinct=True)
        )
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'locked':
            queryset = queryset.filter(
                account_locked_until__gt=timezone.now()
            )
        
        return queryset.order_by('-date_joined')
    
    def create(self, request):
        """Create a new user with audit logging."""
        # Validate password complexity
        password = request.data.get('password')
        if not password or not is_password_complex(password):
            return Response(
                {'error': 'Password does not meet complexity requirements'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set created_by
        user = serializer.save(created_by=request.user)
        user.set_password(password)
        user.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            user_role=request.user.role,
            action='USER_CREATED',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            resource=f'User: {user.username}',
            details={
                'new_user_id': user.id,
                'new_user_role': user.role,
                'created_by': request.user.username
            }
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        """Update user with audit logging."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Store original values for audit
        original_data = {
            'role': instance.role,
            'is_active': instance.is_active,
            'department': instance.department
        }
        
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Log changes
        changes = {}
        for field, original_value in original_data.items():
            new_value = getattr(instance, field)
            if original_value != new_value:
                changes[field] = {
                    'from': original_value,
                    'to': new_value
                }
        
        if changes:
            AuditLog.objects.create(
                user=request.user,
                username=request.user.username,
                user_role=request.user.role,
                action='USER_UPDATED',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                resource=f'User: {instance.username}',
                details={
                    'target_user_id': instance.id,
                    'changes': changes,
                    'updated_by': request.user.username
                }
            )
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete user (deactivate) with audit logging."""
        instance = self.get_object()
        
        # Don't allow deleting self
        if instance.id == request.user.id:
            return Response(
                {'error': 'Cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soft delete (deactivate)
        instance.is_active = False
        instance.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            user_role=request.user.role,
            action='USER_DELETED',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            resource=f'User: {instance.username}',
            details={
                'target_user_id': instance.id,
                'deactivated_by': request.user.username
            }
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        """Unlock a locked user account."""
        user = self.get_object()
        
        if not user.is_locked:
            return Response(
                {'message': 'User account is not locked'},
                status=status.HTTP_200_OK
            )
        
        # Unlock account
        user.account_locked_until = None
        user.failed_login_attempts = 0
        user.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            user_role=request.user.role,
            action='ACCOUNT_UNLOCKED',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            resource=f'User: {user.username}',
            details={
                'unlocked_by': request.user.username,
                'target_user_id': user.id
            }
        )
        
        return Response({
            'message': 'User account unlocked successfully',
            'username': user.username
        })
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password (admin action)."""
        user = self.get_object()
        new_password = request.data.get('password')
        
        if not new_password or not is_password_complex(new_password):
            return Response(
                {'error': 'Password does not meet complexity requirements'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            user_role=request.user.role,
            action='PASSWORD_CHANGED',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            resource=f'User: {user.username}',
            details={
                'reset_by': request.user.username,
                'target_user_id': user.id,
                'admin_reset': True
            }
        )
        
        return Response({
            'message': 'Password reset successfully',
            'username': user.username
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get user statistics for admin dashboard."""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        locked_users = User.objects.filter(
            account_locked_until__gt=timezone.now()
        ).count()
        
        # Users by role
        users_by_role = User.objects.values('role').annotate(
            count=Count('id')
        ).order_by('role')
        
        # Recent activity
        last_24h = timezone.now() - timedelta(hours=24)
        recent_logins = AuditLog.objects.filter(
            action='LOGIN_SUCCESS',
            timestamp__gte=last_24h
        ).count()
        
        # Failed login attempts
        failed_attempts = AuditLog.objects.filter(
            action='LOGIN_FAILED',
            timestamp__gte=last_24h
        ).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'locked_users': locked_users,
            'users_by_role': users_by_role,
            'recent_logins': recent_logins,
            'failed_attempts_24h': failed_attempts,
            'new_users_this_week': User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=7)
            ).count()
        })


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.
    Read-only access for compliance.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrPI]
    
    def get_queryset(self):
        """Filter audit logs."""
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action
        action = self.request.query_params.get('action', None)
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filter by success/failure
        success = self.request.query_params.get('success', None)
        if success is not None:
            queryset = queryset.filter(success=success == 'true')
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get audit log summary for dashboard."""
        last_24h = timezone.now() - timedelta(hours=24)
        last_7d = timezone.now() - timedelta(days=7)
        
        # Activity by action type
        activity_summary = AuditLog.objects.filter(
            timestamp__gte=last_7d
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Failed activities
        failed_activities = AuditLog.objects.filter(
            success=False,
            timestamp__gte=last_24h
        ).count()
        
        # Most active users
        active_users = AuditLog.objects.filter(
            timestamp__gte=last_7d
        ).values('username').annotate(
            activity_count=Count('id')
        ).order_by('-activity_count')[:10]
        
        return Response({
            'activity_summary': activity_summary,
            'failed_activities_24h': failed_activities,
            'most_active_users': active_users,
            'total_events_7d': AuditLog.objects.filter(
                timestamp__gte=last_7d
            ).count()
        })