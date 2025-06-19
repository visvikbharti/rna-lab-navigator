"""
WebSocket consumers for real-time document processing updates.
"""

import json
import logging
from typing import Dict, Any
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache

from .advanced_processor import AdvancedDocumentProcessor, BatchDocumentProcessor
from ..models import Document


logger = logging.getLogger(__name__)


class DocumentProcessingConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time document processing updates.
    Supports individual and batch processing with progress tracking.
    """
    
    async def connect(self):
        """Accept WebSocket connection."""
        self.processing_id = self.scope['url_route']['kwargs'].get('processing_id')
        self.room_group_name = f'processing_{self.processing_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial status
        await self.send_json({
            'type': 'connection',
            'status': 'connected',
            'processing_id': self.processing_id
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnect."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        message_type = content.get('type')
        
        if message_type == 'start_processing':
            await self.start_processing(content.get('data', {}))
        elif message_type == 'start_batch':
            await self.start_batch_processing(content.get('data', {}))
        elif message_type == 'get_status':
            await self.send_status()
        elif message_type == 'cancel':
            await self.cancel_processing()
    
    async def start_processing(self, data: Dict[str, Any]):
        """
        Start processing a single document.
        
        Expected data:
        - file_path: str
        - metadata: dict
        - options: dict (enable_ocr, extract_figures, etc.)
        """
        try:
            file_path = data.get('file_path')
            metadata = data.get('metadata', {})
            options = data.get('options', {})
            
            if not file_path:
                await self.send_error("No file path provided")
                return
            
            # Create processor with WebSocket callback
            processor = AdvancedDocumentProcessor(
                websocket_channel=self
            )
            
            # Start processing
            document, chunk_ids = await processor.process_document(
                file_path=file_path,
                metadata=metadata,
                enable_ocr=options.get('enable_ocr', True),
                extract_figures=options.get('extract_figures', True),
                chunk_size=options.get('chunk_size', 400),
                chunk_overlap=options.get('chunk_overlap', 100)
            )
            
            # Send completion message
            await self.send_json({
                'type': 'completed',
                'data': {
                    'document_id': document.id,
                    'title': document.title,
                    'chunk_count': len(chunk_ids),
                    'processing_time': processor.progress.elapsed_time
                }
            })
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            await self.send_error(str(e))
    
    async def start_batch_processing(self, data: Dict[str, Any]):
        """
        Start batch processing of multiple documents.
        
        Expected data:
        - files: list of {file_path, metadata} dicts
        - options: dict (enable_ocr, extract_figures, etc.)
        """
        try:
            files = data.get('files', [])
            options = data.get('options', {})
            
            if not files:
                await self.send_error("No files provided")
                return
            
            # Extract file paths and metadata
            file_paths = [f['file_path'] for f in files]
            metadata_list = [f.get('metadata', {}) for f in files]
            
            # Create batch processor
            batch_processor = BatchDocumentProcessor(
                max_concurrent=options.get('max_concurrent', 3)
            )
            
            # Process batch
            results = await batch_processor.process_batch(
                file_paths=file_paths,
                metadata_list=metadata_list,
                enable_ocr=options.get('enable_ocr', True),
                extract_figures=options.get('extract_figures', True),
                chunk_size=options.get('chunk_size', 400),
                chunk_overlap=options.get('chunk_overlap', 100)
            )
            
            # Send batch completion
            await self.send_json({
                'type': 'batch_completed',
                'data': results
            })
            
        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}")
            await self.send_error(str(e))
    
    async def send_status(self):
        """Send current processing status."""
        # Get status from cache
        status_key = f"processing_status_{self.processing_id}"
        status = cache.get(status_key, {})
        
        await self.send_json({
            'type': 'status',
            'data': status
        })
    
    async def cancel_processing(self):
        """Cancel ongoing processing."""
        # Set cancellation flag in cache
        cancel_key = f"processing_cancel_{self.processing_id}"
        cache.set(cancel_key, True, timeout=300)
        
        await self.send_json({
            'type': 'cancelled',
            'message': 'Processing cancelled'
        })
    
    async def send_error(self, error_message: str):
        """Send error message."""
        await self.send_json({
            'type': 'error',
            'message': error_message
        })
    
    # Handler for progress updates from processor
    async def processing_progress(self, event):
        """Handle progress updates from channel layer."""
        await self.send_json({
            'type': 'progress',
            'data': event['data']
        })


class DocumentValidationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for document validation and preview.
    Provides real-time feedback during upload.
    """
    
    async def connect(self):
        await self.accept()
    
    async def receive_json(self, content):
        """Handle validation requests."""
        message_type = content.get('type')
        
        if message_type == 'validate':
            await self.validate_document(content.get('data', {}))
        elif message_type == 'preview':
            await self.preview_document(content.get('data', {}))
    
    async def validate_document(self, data: Dict[str, Any]):
        """
        Validate document before processing.
        
        Expected data:
        - file_path: str
        - file_size: int (bytes)
        - file_type: str
        """
        try:
            file_path = data.get('file_path')
            file_size = data.get('file_size', 0)
            file_type = data.get('file_type', '')
            
            validation_results = {
                'valid': True,
                'warnings': [],
                'errors': [],
                'suggestions': []
            }
            
            # Check file size
            max_size = 200 * 1024 * 1024  # 200MB
            if file_size > max_size:
                validation_results['errors'].append(
                    f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (200MB)"
                )
                validation_results['valid'] = False
            elif file_size > 50 * 1024 * 1024:  # Warning for files > 50MB
                validation_results['warnings'].append(
                    "Large file detected. Processing may take longer."
                )
            
            # Check file type
            supported_types = ['pdf', 'docx', 'pptx', 'txt', 'md']
            if file_type.lower() not in supported_types:
                validation_results['errors'].append(
                    f"Unsupported file type: {file_type}"
                )
                validation_results['valid'] = False
            
            # Additional checks
            if file_type.lower() == 'pdf':
                # Check if PDF is encrypted or corrupted
                try:
                    import fitz
                    doc = fitz.open(file_path)
                    if doc.is_encrypted:
                        validation_results['errors'].append(
                            "PDF is encrypted. Please provide an unencrypted version."
                        )
                        validation_results['valid'] = False
                    
                    page_count = len(doc)
                    if page_count > 500:
                        validation_results['warnings'].append(
                            f"Document has {page_count} pages. Consider splitting for better performance."
                        )
                    
                    # Check if OCR might be needed
                    text_sample = doc[0].get_text() if page_count > 0 else ""
                    if len(text_sample.strip()) < 100:
                        validation_results['suggestions'].append(
                            "Document appears to be scanned. OCR will be enabled automatically."
                        )
                    
                    doc.close()
                    
                except Exception as e:
                    validation_results['errors'].append(
                        f"Failed to read PDF: {str(e)}"
                    )
                    validation_results['valid'] = False
            
            await self.send_json({
                'type': 'validation_result',
                'data': validation_results
            })
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            await self.send_json({
                'type': 'error',
                'message': f"Validation failed: {str(e)}"
            })
    
    async def preview_document(self, data: Dict[str, Any]):
        """
        Generate document preview.
        
        Expected data:
        - file_path: str
        - preview_pages: int (default: 3)
        """
        try:
            file_path = data.get('file_path')
            preview_pages = data.get('preview_pages', 3)
            
            preview_data = {
                'title': '',
                'page_count': 0,
                'text_preview': '',
                'metadata': {},
                'figures_found': 0
            }
            
            # Extract preview based on file type
            file_type = data.get('file_type', 'pdf').lower()
            
            if file_type == 'pdf':
                import fitz
                doc = fitz.open(file_path)
                
                preview_data['page_count'] = len(doc)
                preview_data['title'] = doc.metadata.get('title', '')
                preview_data['metadata'] = doc.metadata
                
                # Extract text from first few pages
                text_parts = []
                for i in range(min(preview_pages, len(doc))):
                    text = doc[i].get_text()
                    if text.strip():
                        text_parts.append(f"Page {i+1}:\n{text[:500]}...")
                
                preview_data['text_preview'] = '\n\n'.join(text_parts)
                
                # Count figures
                for page in doc:
                    preview_data['figures_found'] += len(page.get_images())
                
                doc.close()
            
            await self.send_json({
                'type': 'preview_result',
                'data': preview_data
            })
            
        except Exception as e:
            logger.error(f"Preview error: {str(e)}")
            await self.send_json({
                'type': 'error',
                'message': f"Preview failed: {str(e)}"
            })