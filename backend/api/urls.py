from django.urls import path, include
from rest_framework.routers import DefaultRouter

# For the demo, use simplified views to avoid dependency issues
from .views_simplified import (
    HealthCheckView, 
    QueryView, 
    FeedbackViewSet,
    QueryHistoryViewSet,
    QueryCacheView,
    FigureViewSet,
    DocumentPreviewView
)

# DRF router for ViewSets
router = DefaultRouter()
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'history', QueryHistoryViewSet, basename='query-history')
router.register(r'figures', FigureViewSet, basename='figure')

urlpatterns = [
    # Core API endpoints
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("query/", QueryView.as_view(), name="query"),
    path("cache/", QueryCacheView.as_view(), name="query-cache"),
    
    # Document endpoints
    path("documents/<int:document_id>/preview/", DocumentPreviewView.as_view(), name="document-preview"),
    
    # Evaluation endpoints removed for demo
    
    # Authentication endpoints
    path("auth/", include("api.auth.urls")),
    
    # Analytics endpoints
    path("analytics/", include("api.analytics.urls")),
    
    # Security audit endpoints
    path("security/", include("api.security.urls")),
    
    # Quality improvement endpoints (simplified for demo)
    path("quality/", include("api.quality.urls_simplified")),
    
    # Enhanced search endpoints (simplified for demo)
    path("search/", include("api.search.urls_simplified")),
    
    # Router URLs
    path("", include(router.urls)),
]