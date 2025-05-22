"""
Analytics hooks for integrating with core components.
Provides functions to collect analytics from key system operations.
"""

import time
import logging
from functools import wraps
from django.utils import timezone

from .collectors import (
    MetricsCollector,
    ActivityCollector,
    AuditCollector,
    SecurityCollector
)

logger = logging.getLogger(__name__)


def measure_query_time(func=None, query_type="vector"):
    """
    Decorator to measure query execution time and record as a metric.
    
    Args:
        func: Function to decorate
        query_type: Type of query (vector, fulltext, hybrid)
    
    Returns:
        Decorated function with query time measurement
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start timing
            start_time = time.time()
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Calculate elapsed time
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Extract user if available (from self.request.user for views)
            user_id = None
            try:
                # Check if 'self' is in args and has request attribute
                if args and hasattr(args[0], 'request') and hasattr(args[0].request, 'user'):
                    user = args[0].request.user
                    user_id = user.id if user and user.is_authenticated else None
            except Exception:
                pass
            
            # Record the metric
            try:
                MetricsCollector.record_query_latency(
                    query_type=query_type,
                    latency_ms=elapsed_ms,
                    user_id=user_id,
                    metadata={
                        'query_args': str(kwargs)[:100]  # Truncate to prevent large data
                    }
                )
            except Exception as e:
                logger.error(f"Error recording query time metric: {str(e)}")
            
            return result
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def measure_llm_time(func=None, model=None):
    """
    Decorator to measure LLM execution time and record as a metric.
    
    Args:
        func: Function to decorate
        model: LLM model name (optional, will try to extract from args/kwargs)
    
    Returns:
        Decorated function with LLM time measurement
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start timing
            start_time = time.time()
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Calculate elapsed time
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Extract model if not provided
            model_name = model
            if not model_name:
                # Try to extract from kwargs
                model_name = kwargs.get('model', 'unknown')
            
            # Extract token counts if available in the result
            prompt_tokens = 0
            completion_tokens = 0
            try:
                if hasattr(result, 'usage'):
                    prompt_tokens = getattr(result.usage, 'prompt_tokens', 0)
                    completion_tokens = getattr(result.usage, 'completion_tokens', 0)
                elif isinstance(result, dict) and 'usage' in result:
                    prompt_tokens = result['usage'].get('prompt_tokens', 0)
                    completion_tokens = result['usage'].get('completion_tokens', 0)
            except Exception:
                pass
            
            # Record the metric
            try:
                MetricsCollector.record_llm_generation_time(
                    model=model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    time_ms=elapsed_ms
                )
            except Exception as e:
                logger.error(f"Error recording LLM time metric: {str(e)}")
            
            return result
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def measure_vector_search_time(func=None, collection=None):
    """
    Decorator to measure vector search time and record as a metric.
    
    Args:
        func: Function to decorate
        collection: Vector collection name (optional, will try to extract from args/kwargs)
    
    Returns:
        Decorated function with vector search time measurement
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start timing
            start_time = time.time()
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Calculate elapsed time
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Extract collection if not provided
            collection_name = collection
            if not collection_name and 'collection_name' in kwargs:
                collection_name = kwargs['collection_name']
            elif not collection_name and len(args) > 0 and isinstance(args[0], str):
                collection_name = args[0]
            else:
                collection_name = 'unknown'
            
            # Extract other metadata
            top_k = kwargs.get('top_k', kwargs.get('limit', 10))
            num_vectors = 0  # This would need to be provided or looked up
            
            # Record the metric
            try:
                MetricsCollector.record_vector_search_time(
                    collection=collection_name,
                    num_vectors=num_vectors,
                    top_k=top_k,
                    time_ms=elapsed_ms
                )
            except Exception as e:
                logger.error(f"Error recording vector search time metric: {str(e)}")
            
            return result
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_document_access(func=None, document_type=None):
    """
    Decorator to log document access events.
    
    Args:
        func: Function to decorate
        document_type: Type of document (thesis, paper, protocol, etc.)
    
    Returns:
        Decorated function with document access logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Call the function
            result = func(*args, **kwargs)
            
            # Extract user and document info
            try:
                # Check if 'self' is in args and has request attribute
                if args and hasattr(args[0], 'request') and hasattr(args[0].request, 'user'):
                    user = args[0].request.user
                    
                    # Extract document ID
                    doc_id = None
                    if 'pk' in kwargs:
                        doc_id = kwargs['pk']
                    elif 'id' in kwargs:
                        doc_id = kwargs['id']
                    elif 'document_id' in kwargs:
                        doc_id = kwargs['document_id']
                    
                    # Extract IP address
                    ip_address = None
                    if hasattr(args[0].request, 'META'):
                        x_forwarded_for = args[0].request.META.get('HTTP_X_FORWARDED_FOR')
                        if x_forwarded_for:
                            ip_address = x_forwarded_for.split(',')[0]
                        else:
                            ip_address = args[0].request.META.get('REMOTE_ADDR')
                    
                    # Extract session ID
                    session_id = args[0].request.session.session_key if hasattr(args[0].request, 'session') else None
                    
                    # Determine document type
                    doc_type = document_type
                    if not doc_type:
                        if 'document_type' in kwargs:
                            doc_type = kwargs['document_type']
                        else:
                            # Try to infer from the URL or view name
                            path = args[0].request.path.lower()
                            if 'thesis' in path:
                                doc_type = 'thesis'
                            elif 'paper' in path:
                                doc_type = 'paper'
                            elif 'protocol' in path:
                                doc_type = 'protocol'
                            else:
                                doc_type = 'document'
                    
                    # Log the event
                    if doc_id:
                        ActivityCollector.record_document_view(
                            user=user,
                            document_id=doc_id,
                            document_type=doc_type,
                            ip_address=ip_address,
                            session_id=session_id
                        )
                        
                        # Also log as an audit event for sensitive documents
                        if doc_type in ['thesis', 'confidential']:
                            AuditCollector.record_data_access(
                                user=user,
                                resource_type=doc_type,
                                resource_id=doc_id,
                                action='view',
                                ip_address=ip_address
                            )
            except Exception as e:
                logger.error(f"Error logging document access: {str(e)}")
            
            return result
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_document_upload(func=None, document_type=None):
    """
    Decorator to log document upload events.
    
    Args:
        func: Function to decorate
        document_type: Type of document (thesis, paper, protocol, etc.)
    
    Returns:
        Decorated function with document upload logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Call the function to get the uploaded document
            result = func(*args, **kwargs)
            
            # Extract user and document info
            try:
                # Check if 'self' is in args and has request attribute
                if args and hasattr(args[0], 'request') and hasattr(args[0].request, 'user'):
                    user = args[0].request.user
                    
                    # Extract document info from result
                    doc_id = None
                    filename = None
                    filesize = None
                    
                    if hasattr(result, 'id'):
                        doc_id = result.id
                    elif isinstance(result, dict) and 'id' in result:
                        doc_id = result['id']
                    
                    if hasattr(result, 'filename'):
                        filename = result.filename
                    elif isinstance(result, dict) and 'filename' in result:
                        filename = result['filename']
                    elif 'file' in kwargs and hasattr(kwargs['file'], 'name'):
                        filename = kwargs['file'].name
                    
                    if hasattr(result, 'size') or hasattr(result, 'filesize'):
                        filesize = getattr(result, 'size', getattr(result, 'filesize', None))
                    elif isinstance(result, dict) and ('size' in result or 'filesize' in result):
                        filesize = result.get('size', result.get('filesize'))
                    elif 'file' in kwargs and hasattr(kwargs['file'], 'size'):
                        filesize = kwargs['file'].size
                    
                    # Extract IP address
                    ip_address = None
                    if hasattr(args[0].request, 'META'):
                        x_forwarded_for = args[0].request.META.get('HTTP_X_FORWARDED_FOR')
                        if x_forwarded_for:
                            ip_address = x_forwarded_for.split(',')[0]
                        else:
                            ip_address = args[0].request.META.get('REMOTE_ADDR')
                    
                    # Extract session ID
                    session_id = args[0].request.session.session_key if hasattr(args[0].request, 'session') else None
                    
                    # Determine document type
                    doc_type = document_type
                    if not doc_type:
                        if 'document_type' in kwargs:
                            doc_type = kwargs['document_type']
                        else:
                            # Try to infer from the URL or view name
                            path = args[0].request.path.lower()
                            if 'thesis' in path:
                                doc_type = 'thesis'
                            elif 'paper' in path:
                                doc_type = 'paper'
                            elif 'protocol' in path:
                                doc_type = 'protocol'
                            else:
                                doc_type = 'document'
                    
                    # Log the event
                    if doc_id and filename:
                        ActivityCollector.record_document_upload(
                            user=user,
                            document_id=doc_id,
                            document_type=doc_type,
                            filename=filename,
                            filesize=filesize,
                            ip_address=ip_address,
                            session_id=session_id
                        )
                        
                        # Also log as an audit event
                        AuditCollector.record_data_access(
                            user=user,
                            resource_type=doc_type,
                            resource_id=doc_id,
                            action='upload',
                            ip_address=ip_address,
                            details={'filename': filename, 'filesize': filesize}
                        )
            except Exception as e:
                logger.error(f"Error logging document upload: {str(e)}")
            
            return result
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_query(func=None):
    """
    Decorator to log user queries.
    
    Args:
        func: Function to decorate
    
    Returns:
        Decorated function with query logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start timing
            start_time = time.time()
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Calculate elapsed time
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Extract user and query info
            try:
                # Check if 'self' is in args and has request attribute
                if args and hasattr(args[0], 'request'):
                    request = args[0].request
                    user = request.user
                    
                    # Extract query text
                    query_text = None
                    if request.method == 'POST' and hasattr(request, 'data'):
                        query_text = request.data.get('query', request.data.get('question', None))
                    
                    # Extract IP address
                    ip_address = None
                    if hasattr(request, 'META'):
                        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                        if x_forwarded_for:
                            ip_address = x_forwarded_for.split(',')[0]
                        else:
                            ip_address = request.META.get('REMOTE_ADDR')
                    
                    # Extract session ID
                    session_id = request.session.session_key if hasattr(request, 'session') else None
                    
                    # Extract confidence score from result if available
                    confidence_score = None
                    if hasattr(result, 'data') and isinstance(result.data, dict):
                        confidence_score = result.data.get('confidence_score', None)
                    elif isinstance(result, dict):
                        confidence_score = result.get('confidence_score', None)
                    
                    # Determine success status
                    success = True
                    if hasattr(result, 'status_code') and result.status_code >= 400:
                        success = False
                    
                    # Log the query
                    if query_text:
                        ActivityCollector.record_query(
                            user=user,
                            query_text=query_text,
                            response_time=elapsed_ms,
                            ip_address=ip_address,
                            session_id=session_id,
                            success=success,
                            confidence_score=confidence_score
                        )
            except Exception as e:
                logger.error(f"Error logging query: {str(e)}")
            
            return result
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)