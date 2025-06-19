"""
URL patterns for document ingestion API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentUploadView,
    BatchUploadView,
    DocumentValidationView,
    DocumentPreviewView,
    ProcessingStatusView,
    DocumentViewSet
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

app_name = 'ingestion'

urlpatterns = [
    # Upload endpoints
    path('upload/', DocumentUploadView.as_view(), name='upload'),
    path('batch-upload/', BatchUploadView.as_view(), name='batch-upload'),
    
    # Validation and preview
    path('validate/', DocumentValidationView.as_view(), name='validate'),
    path('preview/', DocumentPreviewView.as_view(), name='preview'),
    
    # Processing status
    path('status/<str:processing_id>/', ProcessingStatusView.as_view(), name='status'),
    
    # Include router URLs
    path('', include(router.urls)),
]