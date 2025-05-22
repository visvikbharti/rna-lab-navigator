"""
Simplified URL patterns for the search app.
"""

from django.urls import path

from .views_simplified import search_view

urlpatterns = [
    path('', search_view, name='search'),
]