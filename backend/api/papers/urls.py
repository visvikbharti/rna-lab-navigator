"""
URL configuration for paper monitoring
"""

from django.urls import path
from . import views

app_name = 'papers'

urlpatterns = [
    # Dashboard and overview
    path('dashboard/', views.paper_dashboard, name='dashboard'),
    path('list/', views.get_papers, name='list'),
    path('stats/', views.paper_stats, name='stats'),
    
    # Individual paper operations
    path('<uuid:paper_id>/', views.paper_detail, name='detail'),
    
    # Management operations
    path('check-now/', views.check_papers_now, name='check_now'),
    path('keywords/', views.manage_keywords, name='keywords'),
    path('digest/', views.generate_digest, name='digest'),
]