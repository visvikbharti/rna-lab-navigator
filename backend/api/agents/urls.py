"""
URL configuration for multi-agent research system
"""

from django.urls import path
from . import views

urlpatterns = [
    # Individual agent endpoints
    path('analyze-literature/', views.analyze_literature, name='analyze_literature'),
    path('generate-hypothesis/', views.generate_hypothesis, name='generate_hypothesis'),
    path('design-protocol/', views.design_protocol, name='design_protocol'),
    path('critique/', views.critique_research, name='critique_research'),
    path('find-contradictions/', views.find_contradictions, name='find_contradictions'),
    
    # Orchestrated workflows
    path('orchestrate/', views.orchestrate_research, name='orchestrate_research'),
    path('cross-paper-analysis/', views.cross_paper_analysis, name='cross_paper_analysis'),
]