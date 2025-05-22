"""
URL patterns for the analytics app.
Defines endpoints for analytics data and dashboard.
"""

from django.urls import path
from .views import (
    DashboardDataView,
    system_health_view,
    query_analytics_view,
    security_analytics_view
)

urlpatterns = [
    # API endpoints for dashboard data
    path('dashboard/data/', DashboardDataView.as_view(), name='dashboard_data'),
    path('system/health/', system_health_view, name='system_health'),
    path('queries/analytics/', query_analytics_view, name='query_analytics'),
    path('security/analytics/', security_analytics_view, name='security_analytics'),
]