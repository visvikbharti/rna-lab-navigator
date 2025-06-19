"""
API views for document ingestion with advanced features.
"""

import os
import uuid
import asyncio
from typing import Dict, Any
import tempfile
import logging

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.cache import cache
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from channels.layers import get_channel_layer
from celery import shared_task

from .serializers import (
    DocumentUploadSerializer,
    BatchUploadSerializer,
    ProcessingOptionsSerializer,
    DocumentSerializer,
    FigureSerializer,
    ProcessingStatusSerializer,
    ValidationResultSerializer,
    DocumentPreviewSerializer
)
from .advanced_processor import AdvancedDocumentProcessor, BatchDocumentProcessor
from ..models import Document, Figure


logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class DocumentUploadView(APIView):
    """
    Upload and process single documents with real-time progress updates.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle document upload."""
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Save uploaded file
        uploaded_file = serializer.validated_data['file']
        metadata = serializer.validated_data['metadata']
        options = serializer.validated_data.get('options', {})
        
        # Generate unique processing ID
        processing_id = str(uuid.uuid4())
        
        # Save file to temporary location
        temp_path = default_storage.save(
            f'temp/{processing_id}/{uploaded_file.name}',
            uploaded_file
        )
        file_path = default_storage.path(temp_path)
        
        # Start async processing
        process_document_async.delay(
            file_path=file_path,
            metadata=metadata,
            options=options,
            processing_id=processing_id,
            user_id=request.user.id
        )
        
        # Return processing ID for WebSocket connection
        return Response({
            'processing_id': processing_id,
            'websocket_url': f'/ws/processing/{processing_id}/',
            'status': 'processing'
        }, status=status.HTTP_202_ACCEPTED)


class BatchUploadView(APIView):
    """
    Upload and process multiple documents in batch.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle batch upload."""
        serializer = BatchUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        files = serializer.validated_data['files']
        metadata_list = serializer.validated_data['metadata_list']
        options = serializer.validated_data.get('options', {})
        
        # Generate batch ID
        batch_id = str(uuid.uuid4())
        
        # Save files
        file_paths = []
        for idx, file in enumerate(files):
            temp_path = default_storage.save(
                f'temp/{batch_id}/{file.name}',
                file
            )
            file_paths.append(default_storage.path(temp_path))
        
        # Start batch processing
        process_batch_async.delay(
            file_paths=file_paths,
            metadata_list=metadata_list,
            options=options,
            batch_id=batch_id,
            user_id=request.user.id
        )
        
        return Response({
            'batch_id': batch_id,
            'websocket_url': f'/ws/processing/{batch_id}/',
            'file_count': len(files),
            'status': 'processing'
        }, status=status.HTTP_202_ACCEPTED)


class DocumentValidationView(APIView):
    """
    Validate documents before processing.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Validate uploaded document."""
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save to temp for validation
        temp_path = default_storage.save(
            f'temp/validation/{file.name}',
            file
        )
        file_path = default_storage.path(temp_path)
        
        try:
            # Run validation
            validation_results = validate_document_sync(file_path, file.size)
            
            # Clean up temp file
            default_storage.delete(temp_path)
            
            serializer = ValidationResultSerializer(validation_results)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            default_storage.delete(temp_path)
            return Response(
                {'error': f'Validation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentPreviewView(APIView):
    """
    Generate document preview before processing.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Generate document preview."""
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        preview_pages = int(request.data.get('preview_pages', 3))
        
        # Save to temp for preview
        temp_path = default_storage.save(
            f'temp/preview/{file.name}',
            file
        )
        file_path = default_storage.path(temp_path)
        
        try:
            # Generate preview
            preview_data = generate_preview_sync(file_path, preview_pages)
            
            # Clean up temp file
            default_storage.delete(temp_path)
            
            serializer = DocumentPreviewSerializer(preview_data)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Preview error: {str(e)}")
            default_storage.delete(temp_path)
            return Response(
                {'error': f'Preview failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessingStatusView(APIView):
    """
    Get processing status for a document or batch.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, processing_id):
        """Get processing status."""
        # Get status from cache
        status_key = f"processing_status_{processing_id}"
        status_data = cache.get(status_key)
        
        if not status_data:
            return Response(
                {'error': 'Processing ID not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProcessingStatusSerializer(status_data)
        return Response(serializer.data)


class DocumentViewSet(ModelViewSet):
    """
    ViewSet for Document model with additional actions.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def figures(self, request, pk=None):
        """Get all figures for a document."""
        document = self.get_object()
        figures = document.figures.all()
        serializer = FigureSerializer(figures, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocess a document."""
        document = self.get_object()
        options = ProcessingOptionsSerializer(data=request.data)
        
        if not options.is_valid():
            return Response(options.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Start reprocessing task
        processing_id = str(uuid.uuid4())
        reprocess_document_task.delay(
            document_id=document.id,
            options=options.validated_data,
            processing_id=processing_id
        )
        
        return Response({
            'processing_id': processing_id,
            'websocket_url': f'/ws/processing/{processing_id}/',
            'status': 'reprocessing'
        }, status=status.HTTP_202_ACCEPTED)


from .tasks import process_document_async, process_batch_async


# Helper functions
def update_progress(processing_id: str, progress: Dict[str, Any]):
    """Update processing progress in cache."""
    status_key = f"processing_status_{processing_id}"
    cache.set(status_key, progress, timeout=3600)  # 1 hour TTL


def validate_document_sync(file_path: str, file_size: int) -> Dict[str, Any]:
    """Synchronous document validation."""
    # Implementation of validation logic
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'suggestions': []
    }
    
    # Add validation logic here
    
    return validation_results


def generate_preview_sync(file_path: str, preview_pages: int) -> Dict[str, Any]:
    """Synchronous document preview generation."""
    # Implementation of preview generation
    preview_data = {
        'title': '',
        'page_count': 0,
        'text_preview': '',
        'metadata': {},
        'figures_found': 0
    }
    
    # Add preview generation logic here
    
    return preview_data