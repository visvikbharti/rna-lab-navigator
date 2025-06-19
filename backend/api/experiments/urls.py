"""
URL configuration for Experiment Mapping
"""

from django.urls import path
from . import views
from . import intelligent_design

app_name = 'experiments'

urlpatterns = [
    path('map/', views.map_experiments, name='map_experiments'),
    path('analyze-single/', views.analyze_single_experiment, name='analyze_single'),
    path('quick-factor-analysis/', views.quick_factor_analysis, name='quick_factor_analysis'),
    path('status/', views.experiment_mapping_status, name='status'),
    
    # Intelligent experiment design endpoints
    path('design/', intelligent_design.design_experiment, name='design_experiment'),
    path('validate/', intelligent_design.validate_protocol, name='validate_protocol'),
    path('pilot/', intelligent_design.suggest_pilot_experiment, name='suggest_pilot'),
]