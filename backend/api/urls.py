from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .simple_auth import simple_login

# For the demo, use simplified views to avoid dependency issues
from .views_simplified import (
    HealthCheckView, 
    QueryView, 
    TestRAGView,
    FeedbackViewSet,
    QueryHistoryViewSet,
    QueryCacheView,
    FigureViewSet,
    DocumentPreviewView
)
from . import views  # Import main views for MultiHopQueryView

# Import enhanced views
try:
    from .views_enhanced import EnhancedQueryView, EnhancedSystemStatusView
    enhanced_views_available = True
except ImportError:
    enhanced_views_available = False

# DRF router for ViewSets
router = DefaultRouter()
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'history', QueryHistoryViewSet, basename='query-history')
router.register(r'figures', FigureViewSet, basename='figure')

urlpatterns = [
    # Core API endpoints
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("query/", QueryView.as_view(), name="query"),
    path("query/multihop/", views.MultiHopQueryView.as_view(), name="multihop-query"),
    path("query/enhanced/", views.EnhancedRAGView.as_view(), name="enhanced-rag"),
    path("query/autocomplete/", views.AutocompleteView.as_view(), name="autocomplete"),
    path("query/conversation/<str:session_id>/", views.ConversationHistoryView.as_view(), name="conversation-history"),
    path("test-rag/", TestRAGView.as_view(), name="test-rag"),  # DEBUG endpoint
    path("cache/", QueryCacheView.as_view(), name="query-cache"),
    
    # Document endpoints
    path("documents/<int:document_id>/preview/", DocumentPreviewView.as_view(), name="document-preview"),
    
    # Evaluation endpoints removed for demo
    
    # Authentication endpoints
    path("auth/", include("api.auth.urls")),
    path("auth/simple-login/", simple_login, name="simple-login"),
    
    # Analytics endpoints
    path("analytics/", include("api.analytics.urls")),
    
    # Security audit endpoints
    path("security/", include("api.security.urls")),
    
    # Quality improvement endpoints (simplified for demo)
    path("quality/", include("api.quality.urls_simplified")),
    
    # Enhanced search endpoints (simplified for demo)
    path("search/", include("api.search.urls_simplified")),
    
    # # Hypothesis mode endpoints (TODO: implement)
    # path("hypothesis/", include("api.hypothesis.urls")),
    
    # # Experiment mapping endpoints (TODO: implement)
    # path("experiments/", include("api.experiments.urls")),
    
    # Document ingestion endpoints
    path("ingestion/", include("api.ingestion.urls")),
    
    # # Intelligence endpoints (TODO: implement)
    # path("intelligence/", include("api.intelligence.urls")),
    
    # # Knowledge graph endpoints (TODO: implement)
    # path("knowledge-graph/", include("api.knowledge_graph.urls")),
    
    # Chat endpoints
    path("chat/", include("api.chat.urls")),
    
    # # Paper monitoring endpoints (TODO: implement)
    # path("papers/", include("api.papers.urls")),
    
    # # Multi-agent research system endpoints (TODO: implement)
    # path("agents/", include("api.agents.urls")),
    
    # Router URLs
    path("", include(router.urls)),
]

# Add enhanced RAG endpoints if available
if enhanced_views_available:
    urlpatterns.extend([
        path("query/enhanced-v2/", EnhancedQueryView.as_view(), name="enhanced-query-v2"),
        path("system/enhanced-status/", EnhancedSystemStatusView.as_view(), name="enhanced-system-status"),
    ])