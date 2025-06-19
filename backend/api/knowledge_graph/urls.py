from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.graph_overview, name='graph-overview'),
    path('discover/', views.trigger_discovery, name='trigger-discovery'),
    path('cluster/', views.trigger_clustering, name='trigger-clustering'),
    path('temporal/', views.get_temporal_evolution, name='temporal-evolution'),
    path('search/', views.search_graph, name='search-graph'),
]