"""
Celery tasks for document ingestion with error recovery and monitoring.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

from celery import shared_task, Task
from celery.exceptions import SoftTimeLimitExceeded
from django.core.cache import cache
from django.conf import settings
from channels.layers import get_channel_layer

from .advanced_processor import AdvancedDocumentProcessor, BatchDocumentProcessor
from ..models import Document
from ..intelligence.knowledge_graph import get_graph_service


logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class DocumentProcessingTask(Task):
    """Base task class with error handling and monitoring."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        processing_id = kwargs.get('processing_id')
        if processing_id:
            update_processing_status(processing_id, {
                'status': 'failed',
                'error': str(exc),
                'failed_at': datetime.now().isoformat()
            })
        
        logger.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        processing_id = kwargs.get('processing_id')
        if processing_id:
            status = get_processing_status(processing_id)
            retry_count = status.get('retry_count', 0) + 1
            update_processing_status(processing_id, {
                'retry_count': retry_count,
                'last_retry': datetime.now().isoformat(),
                'retry_reason': str(exc)
            })
        
        logger.warning(f"Task {task_id} retrying: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)


@shared_task(
    base=DocumentProcessingTask,
    bind=True,
    max_retries=3,
    soft_time_limit=1800,  # 30 minutes
    time_limit=2100,  # 35 minutes
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def process_document_async(self, file_path: str, metadata: Dict[str, Any], 
                          options: Dict[str, Any], processing_id: str, user_id: int):
    """
    Process a single document asynchronously with retry logic.
    """
    try:
        # Check if cancelled
        if is_processing_cancelled(processing_id):
            logger.info(f"Processing {processing_id} was cancelled")
            update_processing_status(processing_id, {'status': 'cancelled'})
            return
        
        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _process_document(file_path, metadata, options, processing_id)
            )
            return result
        finally:
            loop.close()
            
    except SoftTimeLimitExceeded:
        logger.error(f"Processing {processing_id} exceeded time limit")
        self.retry(countdown=300)  # Retry after 5 minutes
        
    except Exception as exc:
        logger.error(f"Processing {processing_id} failed: {exc}")
        if self.request.retries < self.max_retries:
            # Exponential backoff retry
            self.retry(exc=exc)
        else:
            # Final failure
            update_processing_status(processing_id, {
                'status': 'failed',
                'error': str(exc),
                'final_failure': True
            })
            raise
        
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {file_path}: {e}")


@shared_task(
    base=DocumentProcessingTask,
    bind=True,
    max_retries=2,
    soft_time_limit=7200,  # 2 hours for batch
    time_limit=7500,
)
def process_batch_async(self, file_paths: List[str], metadata_list: List[Dict[str, Any]],
                       options: Dict[str, Any], batch_id: str, user_id: int):
    """
    Process a batch of documents with partial failure recovery.
    """
    try:
        # Check if cancelled
        if is_processing_cancelled(batch_id):
            logger.info(f"Batch {batch_id} was cancelled")
            update_processing_status(batch_id, {'status': 'cancelled'})
            return
        
        # Run async batch processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _process_batch(file_paths, metadata_list, options, batch_id)
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Batch {batch_id} failed: {exc}")
        if self.request.retries < self.max_retries:
            # Retry with remaining files only
            failed_indices = get_failed_indices(batch_id)
            if failed_indices:
                remaining_files = [file_paths[i] for i in failed_indices]
                remaining_metadata = [metadata_list[i] for i in failed_indices]
                self.retry(args=[remaining_files, remaining_metadata, options, batch_id, user_id])
        else:
            update_processing_status(batch_id, {
                'status': 'partial_failure',
                'error': str(exc)
            })
            raise
        
    finally:
        # Cleanup temp files
        cleanup_temp_files(file_paths)


@shared_task
def cleanup_old_processing_data():
    """
    Periodic task to clean up old processing data.
    """
    cutoff_date = datetime.now() - timedelta(days=7)
    
    # Get all processing keys
    pattern = 'processing_status_*'
    for key in cache.iter_keys(pattern):
        status = cache.get(key)
        if status and 'created_at' in status:
            created = datetime.fromisoformat(status['created_at'])
            if created < cutoff_date:
                cache.delete(key)
                logger.info(f"Cleaned up old processing data: {key}")


@shared_task
def monitor_processing_health():
    """
    Monitor processing health and alert on issues.
    """
    stats = {
        'active_processing': 0,
        'stuck_processing': 0,
        'failed_last_hour': 0
    }
    
    # Check all processing statuses
    pattern = 'processing_status_*'
    for key in cache.iter_keys(pattern):
        status = cache.get(key)
        if not status:
            continue
            
        if status.get('status') == 'processing':
            stats['active_processing'] += 1
            
            # Check if stuck (no update for 30 minutes)
            last_update = status.get('last_update')
            if last_update:
                last_update_time = datetime.fromisoformat(last_update)
                if datetime.now() - last_update_time > timedelta(minutes=30):
                    stats['stuck_processing'] += 1
        
        elif status.get('status') == 'failed':
            failed_at = status.get('failed_at')
            if failed_at:
                failed_time = datetime.fromisoformat(failed_at)
                if datetime.now() - failed_time < timedelta(hours=1):
                    stats['failed_last_hour'] += 1
    
    # Store stats
    cache.set('processing_health_stats', stats, timeout=300)
    
    # Alert if issues
    if stats['stuck_processing'] > 0 or stats['failed_last_hour'] > 5:
        logger.error(f"Processing health alert: {stats}")
        # Send alert notification
    
    return stats


# Helper functions
async def _process_document(file_path: str, metadata: Dict[str, Any],
                           options: Dict[str, Any], processing_id: str):
    """Process document with progress updates."""
    processor = AdvancedDocumentProcessor(
        progress_callback=lambda progress: asyncio.create_task(
            update_progress_async(processing_id, progress)
        )
    )
    
    # Initialize status
    update_processing_status(processing_id, {
        'status': 'processing',
        'created_at': datetime.now().isoformat(),
        'file_path': file_path,
        'metadata': metadata
    })
    
    try:
        document, chunk_ids = await processor.process_document(
            file_path=file_path,
            metadata=metadata,
            **options
        )
        
        # Update final status
        update_processing_status(processing_id, {
            'status': 'completed',
            'document_id': document.id,
            'chunk_count': len(chunk_ids),
            'completed_at': datetime.now().isoformat(),
            'processing_time': processor.progress.elapsed_time
        })
        
        # Update knowledge graph
        try:
            graph_service = get_graph_service()
            node_id = graph_service.add_document_node(document)
            
            # Generate connections to existing documents
            await generate_graph_connections(document.id)
            
            # Send graph update notification via WebSocket
            await send_graph_update_notification(node_id, document)
        except Exception as e:
            logger.warning(f"Failed to update knowledge graph: {e}")
            # Don't fail the whole process if graph update fails
        
        # Send completion notification
        await send_completion_notification(processing_id, document.id)
        
        return {
            'document_id': document.id,
            'chunk_count': len(chunk_ids)
        }
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise


async def _process_batch(file_paths: List[str], metadata_list: List[Dict[str, Any]],
                        options: Dict[str, Any], batch_id: str):
    """Process batch with individual file tracking."""
    processor = BatchDocumentProcessor(
        max_concurrent=options.get('max_concurrent', 3)
    )
    
    # Initialize batch status
    update_processing_status(batch_id, {
        'status': 'processing',
        'created_at': datetime.now().isoformat(),
        'total_files': len(file_paths),
        'file_statuses': {}
    })
    
    try:
        results = await processor.process_batch(
            file_paths=file_paths,
            metadata_list=metadata_list,
            **options
        )
        
        # Update final status
        update_processing_status(batch_id, {
            'status': 'completed',
            'results': results,
            'completed_at': datetime.now().isoformat()
        })
        
        # Send completion notification
        await send_batch_completion_notification(batch_id, results)
        
        return results
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise


def update_processing_status(processing_id: str, data: Dict[str, Any]):
    """Update processing status in cache."""
    status_key = f"processing_status_{processing_id}"
    current_status = cache.get(status_key, {})
    current_status.update(data)
    current_status['last_update'] = datetime.now().isoformat()
    cache.set(status_key, current_status, timeout=86400)  # 24 hours


async def update_progress_async(processing_id: str, progress: Dict[str, Any]):
    """Send progress update via WebSocket."""
    try:
        await channel_layer.group_send(
            f'processing_{processing_id}',
            {
                'type': 'processing_progress',
                'data': progress
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send progress update: {e}")


def get_processing_status(processing_id: str) -> Dict[str, Any]:
    """Get processing status from cache."""
    status_key = f"processing_status_{processing_id}"
    return cache.get(status_key, {})


def is_processing_cancelled(processing_id: str) -> bool:
    """Check if processing was cancelled."""
    cancel_key = f"processing_cancel_{processing_id}"
    return cache.get(cancel_key, False)


def get_failed_indices(batch_id: str) -> List[int]:
    """Get indices of failed files in batch."""
    status = get_processing_status(batch_id)
    file_statuses = status.get('file_statuses', {})
    return [int(idx) for idx, status in file_statuses.items() if status == 'failed']


def cleanup_temp_files(file_paths: List[str]):
    """Clean up temporary files."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {file_path}: {e}")


async def send_completion_notification(processing_id: str, document_id: int):
    """Send completion notification via WebSocket."""
    try:
        await channel_layer.group_send(
            f'processing_{processing_id}',
            {
                'type': 'processing.complete',
                'document_id': document_id
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send completion notification: {e}")


async def send_batch_completion_notification(batch_id: str, results: Dict[str, Any]):
    """Send batch completion notification via WebSocket."""
    try:
        await channel_layer.group_send(
            f'processing_{batch_id}',
            {
                'type': 'batch.complete',
                'results': results
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send batch completion notification: {e}")


@shared_task
def generate_graph_connections(document_id: int):
    """Generate knowledge graph connections for a document."""
    try:
        graph_service = get_graph_service()
        document = Document.objects.get(id=document_id)
        node_id = f"doc_{document.id}"
        
        # Get suggestions for this node
        suggestions = graph_service.suggest_connections(node_id, limit=10)
        
        # Create connections based on suggestions
        for suggestion in suggestions:
            if suggestion['similarity_score'] > 5:  # Threshold for auto-connection
                for conn_type in suggestion['potential_connection_types']:
                    graph_service.add_connection(
                        node_id,
                        suggestion['node_id'],
                        conn_type,
                        {
                            'auto_generated': True,
                            'similarity_score': suggestion['similarity_score'],
                            'shared_keywords': suggestion['shared_keywords'],
                            'shared_entities': suggestion['shared_entities']
                        }
                    )
        
        logger.info(f"Generated {len(suggestions)} potential connections for document {document_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate graph connections: {e}")


async def send_graph_update_notification(node_id: str, document: Document):
    """Send knowledge graph update notification via WebSocket."""
    try:
        await channel_layer.group_send(
            'knowledge_graph_updates',
            {
                'type': 'new_node',
                'data': {
                    'node_id': node_id,
                    'title': document.title,
                    'doc_type': document.doc_type,
                    'author': document.author,
                    'year': document.year
                }
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send graph update notification: {e}")