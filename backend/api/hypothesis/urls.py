"""
URL configuration for Hypothesis Mode
"""

from django.urls import path
from . import views

app_name = 'hypothesis'

urlpatterns = [
    path('explore/', views.explore_hypothesis, name='explore'),
    # Temporarily disabled for testing
    # path('explore-enhanced/', views.explore_hypothesis_enhanced, name='explore_enhanced'),
    path('generate-protocol/', views.generate_protocol, name='generate_protocol'),
    # path('generate-protocol-enhanced/', views.generate_protocol_enhanced, name='generate_protocol_enhanced'),
    path('status/', views.hypothesis_status, name='status'),
]