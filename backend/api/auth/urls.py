"""
Authentication URLs for the RNA Lab Navigator.
Provides JWT token-based authentication and user management endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from .views import (
    UserProfileView,
    UserRegistrationView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserRoleListView,
    UserRoleDetailView,
    UserPermissionListView,
    UserPermissionDetailView,
)

urlpatterns = [
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    # User management endpoints
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('register/', UserRegistrationView.as_view(), name='user_registration'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Password reset endpoints
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Role-based access control endpoints
    path('roles/', UserRoleListView.as_view(), name='user_roles'),
    path('roles/<int:pk>/', UserRoleDetailView.as_view(), name='user_role_detail'),
    path('permissions/', UserPermissionListView.as_view(), name='user_permissions'),
    path('permissions/<int:pk>/', UserPermissionDetailView.as_view(), name='user_permission_detail'),
]