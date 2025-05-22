from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    QuerySuggestionViewSet,
    SearchRankingProfileViewSet,
    EnhancedSearchViewSet,
    SearchAnalyticsViewSet,
    SearchFacetViewSet,
    SavedSearchViewSet
)
from .views_analytics import SearchQualityViewSet

router = DefaultRouter()
router.register(r'suggestions', QuerySuggestionViewSet, basename='query-suggestion')
router.register(r'ranking-profiles', SearchRankingProfileViewSet, basename='ranking-profile')
router.register(r'search', EnhancedSearchViewSet, basename='enhanced-search')
router.register(r'analytics', SearchAnalyticsViewSet, basename='search-analytics')
router.register(r'facets', SearchFacetViewSet, basename='search-facet')
router.register(r'saved-searches', SavedSearchViewSet, basename='saved-search')
router.register(r'quality', SearchQualityViewSet, basename='search-quality')

urlpatterns = [
    path('', include(router.urls)),
]