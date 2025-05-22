"""
URL patterns for the enhanced feedback system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EnhancedFeedbackViewSet,
    FeedbackCategoryViewSet,
    FeedbackThemeViewSet,
    FeedbackAnalysisViewSet,
    FeedbackThemeMappingViewSet
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'feedback', EnhancedFeedbackViewSet, basename='enhanced-feedback')
router.register(r'categories', FeedbackCategoryViewSet, basename='feedback-category')
router.register(r'themes', FeedbackThemeViewSet, basename='feedback-theme')
router.register(r'analysis', FeedbackAnalysisViewSet, basename='feedback-analysis')
router.register(r'mappings', FeedbackThemeMappingViewSet, basename='feedback-theme-mapping')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]