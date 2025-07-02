"""
URL configuration for authentication endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    register,
    logout,
    change_password,
    user_profile,
    update_profile,
    accept_terms,
    check_permissions,
)

app_name = 'auth'

urlpatterns = [
    # JWT Authentication
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout, name='logout'),
    
    # User Management
    path('register/', register, name='register'),
    path('profile/', user_profile, name='user_profile'),
    path('profile/update/', update_profile, name='update_profile'),
    
    # Password Management
    path('change-password/', change_password, name='change_password'),
    
    # Compliance
    path('accept-terms/', accept_terms, name='accept_terms'),
    
    # Permissions
    path('permissions/', check_permissions, name='check_permissions'),
]