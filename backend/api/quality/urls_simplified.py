"""
Simplified URL patterns for the quality app.
"""

from django.urls import path

from .views_simplified import quality_metrics

urlpatterns = [
    path('metrics/', quality_metrics, name='quality-metrics'),
]