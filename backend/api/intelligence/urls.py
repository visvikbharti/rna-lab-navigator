"""
URL patterns for Knowledge Gap Intelligence API
"""

from django.urls import path
from . import views

app_name = 'intelligence'

urlpatterns = [
    # Knowledge gap endpoints
    path('knowledge-gaps/', views.detect_knowledge_gaps, name='knowledge-gaps'),
    path('analyze-gaps/', views.analyze_gaps, name='analyze-gaps'),
    path('gap-analysis/', views.gap_analysis, name='gap-analysis'),
    path('knowledge-gaps/<str:gap_id>/', views.gap_details, name='gap-details'),
    
    # Research opportunities
    path('research-opportunities/', views.research_opportunities, name='research-opportunities'),
    path('suggest-questions/', views.suggest_research_questions, name='suggest-questions'),
    
    # Topic evolution
    path('topic-evolution/', views.topic_evolution, name='topic-evolution'),
    path('knowledge-gap-heatmap/', views.knowledge_gap_heatmap, name='knowledge-gap-heatmap'),
    
    # Cross-paper insights
    path('cross-paper-insights/', views.cross_paper_insights, name='cross-paper-insights'),
    path('research-connections/', views.research_connections, name='research-connections'),
    path('validate-connection/', views.validate_connection, name='validate-connection'),
    path('rank-insights/', views.rank_insights, name='rank-insights'),
    path('trending-connections/', views.trending_connections, name='trending-connections'),
    
    # Knowledge graph endpoints
    path('graph/stats/', views.knowledge_graph_stats, name='graph-stats'),
    path('graph/search/', views.graph_search, name='graph-search'),
    path('graph/node/<str:node_id>/', views.graph_node_detail, name='graph-node-detail'),
    path('graph/suggestions/<str:node_id>/', views.graph_suggestions, name='graph-suggestions'),
    path('graph/export/', views.graph_export, name='graph-export'),
]