"""
URL patterns for the quality improvement API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    QualityAnalysisViewSet,
    QualityImprovementViewSet,
    ImprovedPromptViewSet,
    RetrievalConfigurationViewSet,
    QualityMetricsViewSet
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'analyses', QualityAnalysisViewSet, basename='quality-analysis')
router.register(r'improvements', QualityImprovementViewSet, basename='quality-improvement')
router.register(r'prompts', ImprovedPromptViewSet, basename='improved-prompt')
router.register(r'configurations', RetrievalConfigurationViewSet, basename='retrieval-configuration')
router.register(r'metrics', QualityMetricsViewSet, basename='quality-metrics')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]