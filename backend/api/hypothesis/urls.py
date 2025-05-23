"""
URL configuration for Hypothesis Mode
"""

from django.urls import path
from . import views

app_name = 'hypothesis'

urlpatterns = [
    path('explore/', views.explore_hypothesis, name='explore'),
    path('generate-protocol/', views.generate_protocol, name='generate_protocol'),
    path('status/', views.hypothesis_status, name='status'),
]