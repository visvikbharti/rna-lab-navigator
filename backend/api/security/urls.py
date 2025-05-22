"""
URL patterns for security audit and monitoring.
Provides API endpoints for security dashboard and administration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('events', views.SecurityEventViewSet)
router.register('blocked-ips', views.BlockedIPViewSet)
router.register('incidents', views.SecurityIncidentViewSet)
router.register('waf-alerts', views.WAFAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/summary/', views.security_dashboard_summary, name='security-dashboard-summary'),
    path('health-check/', views.security_health_check, name='security-health-check'),
]