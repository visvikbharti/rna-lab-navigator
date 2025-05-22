"""
Authentication views for the RNA Lab Navigator.
Provides API endpoints for user registration, profile management, and password management.
"""

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .models import UserRole, UserPermission, AccessAttempt
from .permissions import IsAdmin, IsLabManager, CanManageUsers

from api.security.rate_limiting import track_rate_limit
from api.analytics.collectors import AuditCollector, SecurityCollector


class UserRegistrationView(APIView):
    """
    API view for user registration.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Apply rate limiting to prevent registration abuse
        if not track_rate_limit(request, 'registration', limit=5, window=3600):
            return Response(
                {"detail": "Too many registration attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate token for the user
            refresh = RefreshToken.for_user(user)
            
            # Log the registration event
            ip_address = request.META.get('REMOTE_ADDR')
            AuditCollector.record_audit_event(
                event_type="user_management",
                description=f"User registered: {user.username}",
                user=None,
                ip_address=ip_address,
                severity="info",
                details={"username": user.username, "email": user.email}
            )
            
            return Response({
                "detail": "User registered successfully.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API view for user profile management.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user profile details"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile details"""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Log the profile update event
            ip_address = request.META.get('REMOTE_ADDR')
            AuditCollector.record_audit_event(
                event_type="user_management",
                description=f"Profile updated: {request.user.username}",
                user=request.user,
                ip_address=ip_address,
                severity="info",
                details={"fields_updated": list(request.data.keys())}
            )
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API view for changing password.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Apply rate limiting to prevent password change abuse
        if not track_rate_limit(request, 'password_change', limit=5, window=3600):
            return Response(
                {"detail": "Too many password change attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = ChangePasswordSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            # Change the password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            # Log the password change event
            ip_address = request.META.get('REMOTE_ADDR')
            AuditCollector.record_audit_event(
                event_type="user_management",
                description=f"Password changed: {request.user.username}",
                user=request.user,
                ip_address=ip_address,
                severity="info"
            )
            
            return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    API view for requesting a password reset.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Apply rate limiting to prevent password reset abuse
        if not track_rate_limit(request, 'password_reset_request', limit=3, window=3600):
            return Response(
                {"detail": "Too many password reset attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Generate token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Create reset URL (frontend should handle this route)
                reset_url = f"{settings.SITE_URL}/reset-password/{uid}/{token}/"
                
                # Send email with reset URL
                send_mail(
                    subject="RNA Navigator: Reset Password",
                    message=f"Please click the following link to reset your password: {reset_url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                # Log the password reset request (without revealing if user exists for security)
                ip_address = request.META.get('REMOTE_ADDR')
                AuditCollector.record_audit_event(
                    event_type="user_management",
                    description=f"Password reset requested for email: {email}",
                    user=None,
                    ip_address=ip_address,
                    severity="info"
                )
            except User.DoesNotExist:
                # For security, don't reveal if user exists or not
                pass
            
            # For security, always return success regardless of whether user exists
            return Response({"detail": "Password reset email has been sent if the email exists."}, 
                           status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    API view for confirming a password reset.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Apply rate limiting to prevent password reset abuse
        if not track_rate_limit(request, 'password_reset_confirm', limit=5, window=3600):
            return Response(
                {"detail": "Too many password reset attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            uid = serializer.validated_data['uid']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                # Decode user ID
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
                
                # Verify token
                if not default_token_generator.check_token(user, token):
                    return Response({"detail": "Invalid or expired token."}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                # Reset password
                user.set_password(new_password)
                user.save()
                
                # Log the password reset
                ip_address = request.META.get('REMOTE_ADDR')
                AuditCollector.record_audit_event(
                    event_type="user_management",
                    description=f"Password reset completed: {user.username}",
                    user=user,
                    ip_address=ip_address,
                    severity="info"
                )
                
                return Response({"detail": "Password has been reset successfully."}, 
                               status=status.HTTP_200_OK)
            except (User.DoesNotExist, TypeError, ValueError, OverflowError):
                return Response({"detail": "Invalid reset link."}, 
                               status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Role Management Views
class RoleManagementSerializer(serializers.ModelSerializer):
    """
    Serializer for role management.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ('id', 'username', 'email', 'user', 'role', 'description', 'created_at')
        read_only_fields = ('id', 'username', 'email', 'created_at')


class UserRoleListView(APIView):
    """
    API view for listing and creating user roles.
    """
    permission_classes = [IsAuthenticated, IsAdmin | CanManageUsers]
    
    def get(self, request):
        """List all user roles"""
        roles = UserRole.objects.all().select_related('user')
        serializer = RoleManagementSerializer(roles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new user role"""
        serializer = RoleManagementSerializer(data=request.data)
        if serializer.is_valid():
            # Set created_by to the current user
            serializer.validated_data['created_by'] = request.user
            role = serializer.save()
            
            # Log the role creation
            ip_address = request.META.get('REMOTE_ADDR')
            AuditCollector.record_audit_event(
                event_type="user_management",
                description=f"User role created: {role.user.username} - {role.get_role_display()}",
                user=request.user,
                ip_address=ip_address,
                severity="info",
                details={
                    "role": role.role,
                    "username": role.user.username,
                    "description": role.description
                }
            )
            
            return Response(RoleManagementSerializer(role).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRoleDetailView(APIView):
    """
    API view for retrieving, updating and deleting a user role.
    """
    permission_classes = [IsAuthenticated, IsAdmin | CanManageUsers]
    
    def get_object(self, pk):
        return get_object_or_404(UserRole, pk=pk)
    
    def get(self, request, pk):
        """Retrieve a user role"""
        role = self.get_object(pk)
        serializer = RoleManagementSerializer(role)
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Update a user role"""
        role = self.get_object(pk)
        serializer = RoleManagementSerializer(role, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_role = serializer.save()
            
            # Log the role update
            ip_address = request.META.get('REMOTE_ADDR')
            AuditCollector.record_audit_event(
                event_type="user_management",
                description=f"User role updated: {updated_role.user.username} - {updated_role.get_role_display()}",
                user=request.user,
                ip_address=ip_address,
                severity="info",
                details={
                    "role": updated_role.role,
                    "username": updated_role.user.username,
                    "fields_updated": list(request.data.keys())
                }
            )
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Delete a user role"""
        role = self.get_object(pk)
        username = role.user.username
        role_name = role.get_role_display()
        
        role.delete()
        
        # Log the role deletion
        ip_address = request.META.get('REMOTE_ADDR')
        AuditCollector.record_audit_event(
            event_type="user_management",
            description=f"User role deleted: {username} - {role_name}",
            user=request.user,
            ip_address=ip_address,
            severity="warning"
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)


# Permission Management Views
class PermissionManagementSerializer(serializers.ModelSerializer):
    """
    Serializer for permission management.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserPermission
        fields = ('id', 'username', 'email', 'user', 'permission', 'created_at')
        read_only_fields = ('id', 'username', 'email', 'created_at')


class UserPermissionListView(APIView):
    """
    API view for listing and creating user permissions.
    """
    permission_classes = [IsAuthenticated, IsAdmin | CanManageUsers]
    
    def get(self, request):
        """List all user permissions"""
        permissions = UserPermission.objects.all().select_related('user')
        serializer = PermissionManagementSerializer(permissions, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new user permission"""
        serializer = PermissionManagementSerializer(data=request.data)
        if serializer.is_valid():
            # Set granted_by to the current user
            serializer.validated_data['granted_by'] = request.user
            permission = serializer.save()
            
            # Log the permission creation
            ip_address = request.META.get('REMOTE_ADDR')
            AuditCollector.record_audit_event(
                event_type="user_management",
                description=f"User permission granted: {permission.user.username} - {permission.get_permission_display()}",
                user=request.user,
                ip_address=ip_address,
                severity="info",
                details={
                    "permission": permission.permission,
                    "username": permission.user.username
                }
            )
            
            return Response(PermissionManagementSerializer(permission).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPermissionDetailView(APIView):
    """
    API view for retrieving and deleting a user permission.
    """
    permission_classes = [IsAuthenticated, IsAdmin | CanManageUsers]
    
    def get_object(self, pk):
        return get_object_or_404(UserPermission, pk=pk)
    
    def get(self, request, pk):
        """Retrieve a user permission"""
        permission = self.get_object(pk)
        serializer = PermissionManagementSerializer(permission)
        return Response(serializer.data)
    
    def delete(self, request, pk):
        """Delete a user permission"""
        permission = self.get_object(pk)
        username = permission.user.username
        permission_name = permission.get_permission_display()
        
        permission.delete()
        
        # Log the permission deletion
        ip_address = request.META.get('REMOTE_ADDR')
        AuditCollector.record_audit_event(
            event_type="user_management",
            description=f"User permission revoked: {username} - {permission_name}",
            user=request.user,
            ip_address=ip_address,
            severity="warning"
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)