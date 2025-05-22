"""
Simplified URL patterns for the feedback app.
"""

from django.urls import path

from .views_simplified import feedback_summary

urlpatterns = [
    path('summary/', feedback_summary, name='feedback-summary'),
]