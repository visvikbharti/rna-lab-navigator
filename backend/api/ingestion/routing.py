"""
WebSocket routing for document processing.
"""

from django.urls import path
from .consumers import DocumentProcessingConsumer, DocumentValidationConsumer

websocket_urlpatterns = [
    path('ws/processing/<str:processing_id>/', DocumentProcessingConsumer.as_asgi()),
    path('ws/validation/', DocumentValidationConsumer.as_asgi()),
]