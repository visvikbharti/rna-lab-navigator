"""
Security middleware for RNA Lab Navigator.
This middleware intercepts requests and responses to detect and protect against PII exposure.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from io import BytesIO
import re

from django.http import HttpRequest, HttpResponse, JsonResponse, FileResponse
from django.conf import settings
from PIL import Image

from .pii_detector import get_detector

logger = logging.getLogger(__name__)


class PIIFilterMiddleware:
    """
    Middleware that scans content for PII and takes appropriate action.
    - Scans request bodies for PII in uploads
    - Optionally scans responses to prevent PII leakage
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.detector = get_detector()
        self.scan_responses = getattr(settings, 'SCAN_RESPONSES_FOR_PII', False)
        self.scan_requests = getattr(settings, 'SCAN_REQUESTS_FOR_PII', True)
        self.auto_redact = getattr(settings, 'AUTO_REDACT_PII', False)
        
        # Paths to scan
        self.paths_to_scan = [
            '/api/query/',
            '/api/upload/',
            '/api/doc/'
        ]
        
        # Paths to exclude 
        self.excluded_paths = [
            '/api/health/',
            '/api/static/',
            '/api/media/',
            '/api/feedback/'
        ]
        
        logger.info(f"PII Filter Middleware initialized - scan_requests: {self.scan_requests}, "
                    f"scan_responses: {self.scan_responses}, auto_redact: {self.auto_redact}")
    
    def __call__(self, request):
        # Skip middleware for excluded paths
        for excluded in self.excluded_paths:
            if request.path.startswith(excluded):
                return self.get_response(request)
        
        # Flag to indicate if we need to scan this request
        should_scan = any(request.path.startswith(path) for path in self.paths_to_scan)
        
        # Scan request body for PII if enabled
        if self.scan_requests and should_scan and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # Store original request body for later
                request._body_original = request.body
                
                # Handle JSON request bodies
                if request.content_type == 'application/json':
                    # Parse JSON and scan for PII
                    body_dict = json.loads(request.body)
                    scan_result = self._scan_json_data(body_dict)
                    
                    # Handle detected PII
                    if scan_result['has_pii']:
                        if scan_result['risk_level'] == 'high':
                            # Block high-risk content
                            logger.warning(f"Blocked request with high PII risk. "
                                          f"Path: {request.path}, "
                                          f"PII count: {scan_result['pii_count']}")
                            return JsonResponse({
                                "error": "Request contains sensitive information that cannot be processed.",
                                "detail": "Please remove personal information and try again.",
                                "pii_types": list(scan_result['pii_types'].keys())
                            }, status=400)
                        else:
                            # Log medium risk but allow (or redact if enabled)
                            logger.warning(f"Request contains PII. "
                                          f"Path: {request.path}, "
                                          f"PII count: {scan_result['pii_count']}")
                            
                            if self.auto_redact:
                                # Replace request body with redacted version
                                redacted_body = self._redact_json_data(body_dict)
                                request._body = json.dumps(redacted_body).encode('utf-8')
                                
                                # Add header to indicate redaction
                                request.META['HTTP_X_PII_REDACTED'] = 'true'
                
                # Handle multipart form data (file uploads)
                elif request.content_type and 'multipart/form-data' in request.content_type:
                    # Wait until files are parsed
                    response = self.get_response(request)
                    
                    # Process uploaded files
                    for field_name, file_obj in request.FILES.items():
                        # Skip non-text files
                        content_type = file_obj.content_type
                        if not content_type or not (
                            'text' in content_type or 
                            'pdf' in content_type or 
                            'csv' in content_type or 
                            'json' in content_type or
                            'application/octet-stream' in content_type  # Handle files with missing content type
                        ):
                            continue
                            
                        # Skip large files
                        max_scan_size = getattr(settings, 'MAX_PII_SCAN_SIZE', 5 * 1024 * 1024)  # 5MB default
                        if file_obj.size > max_scan_size:
                            logger.warning(f"File too large to scan for PII: {file_obj.name} ({file_obj.size} bytes)")
                            continue
                            
                        # Read file content for scanning
                        file_content = file_obj.read()
                        file_obj.seek(0)  # Reset file pointer
                        
                        # Try to decode as text
                        try:
                            text_content = file_content.decode('utf-8')
                            scan_result = self.detector.scan_document(text_content)
                            
                            if scan_result['has_pii'] and scan_result['risk_level'] == 'high':
                                # Block high-risk uploads
                                logger.warning(f"Blocked file upload with high PII risk. "
                                              f"Filename: {file_obj.name}, "
                                              f"PII count: {scan_result['pii_count']}")
                                return JsonResponse({
                                    "error": "Uploaded file contains sensitive information that cannot be processed.",
                                    "detail": "Please remove personal information and try again.",
                                    "filename": file_obj.name,
                                    "pii_types": list(scan_result['pii_types'].keys())
                                }, status=400)
                                
                        except UnicodeDecodeError:
                            # Not a text file, skip PII scanning
                            pass
                            
                    return response
            
            except Exception as e:
                logger.error(f"Error in PII request filter: {str(e)}")
        
        # Get the response
        response = self.get_response(request)
        
        # Scan response for PII if enabled
        if self.scan_responses and should_scan and hasattr(response, 'content'):
            try:
                # Handle JSON responses
                if hasattr(response, 'content_type') and 'application/json' in response.content_type:
                    response_dict = json.loads(response.content.decode('utf-8'))
                    scan_result = self._scan_json_data(response_dict)
                    
                    if scan_result['has_pii']:
                        logger.warning(f"Response contains PII. "
                                      f"Path: {request.path}, "
                                      f"PII count: {scan_result['pii_count']}")
                        
                        if self.auto_redact:
                            # Replace response with redacted version
                            redacted_content = self._redact_json_data(response_dict)
                            response.content = json.dumps(redacted_content).encode('utf-8')
                            
                            # Add header to indicate redaction
                            response['X-PII-Redacted'] = 'true'
            except Exception as e:
                logger.error(f"Error in PII response filter: {str(e)}")
        
        return response
    
    def _scan_json_data(self, data: Any) -> Dict[str, Any]:
        """
        Recursively scan JSON data for PII.
        
        Args:
            data: JSON data to scan
            
        Returns:
            Dict with scan results
        """
        if isinstance(data, dict):
            # Skip scanning specific fields (like password hashes)
            if 'password' in data or 'token' in data:
                return {"has_pii": False, "pii_count": 0, "pii_types": {}, "risk_level": "low"}
                
            all_results = []
            for key, value in data.items():
                # Skip sensitive keys
                if key in ['password', 'token', 'key', 'secret']:
                    continue
                    
                # Recurse into nested objects and arrays
                if isinstance(value, (dict, list)):
                    result = self._scan_json_data(value)
                    all_results.append(result)
                elif isinstance(value, str) and len(value) > 3:  # Only scan strings with content
                    # Scan the string for PII
                    result = self.detector.scan_document(value)
                    all_results.append(result)
                    
            # Aggregate results
            has_pii = any(r['has_pii'] for r in all_results)
            pii_count = sum(r['pii_count'] for r in all_results)
            
            # Combine PII types
            pii_types = {}
            for result in all_results:
                for pii_type, count in result.get('pii_types', {}).items():
                    pii_types[pii_type] = pii_types.get(pii_type, 0) + count
                    
            # Determine overall risk level
            risk_level = "low"
            if pii_count > 10:
                risk_level = "high"
            elif pii_count > 0:
                risk_level = "medium"
                
            return {
                "has_pii": has_pii,
                "pii_count": pii_count,
                "pii_types": pii_types,
                "risk_level": risk_level
            }
            
        elif isinstance(data, list):
            all_results = [self._scan_json_data(item) for item in data]
            
            # Aggregate results
            has_pii = any(r['has_pii'] for r in all_results)
            pii_count = sum(r['pii_count'] for r in all_results)
            
            # Combine PII types
            pii_types = {}
            for result in all_results:
                for pii_type, count in result.get('pii_types', {}).items():
                    pii_types[pii_type] = pii_types.get(pii_type, 0) + count
                    
            # Determine overall risk level
            risk_level = "low"
            if pii_count > 10:
                risk_level = "high"
            elif pii_count > 0:
                risk_level = "medium"
                
            return {
                "has_pii": has_pii,
                "pii_count": pii_count,
                "pii_types": pii_types,
                "risk_level": risk_level
            }
            
        elif isinstance(data, str) and len(data) > 3:
            # Scan the string for PII
            return self.detector.scan_document(data)
            
        else:
            # Non-string primitive values have no PII
            return {"has_pii": False, "pii_count": 0, "pii_types": {}, "risk_level": "low"}
    
    def _redact_json_data(self, data: Any) -> Any:
        """
        Recursively redact PII from JSON data.
        
        Args:
            data: JSON data to redact
            
        Returns:
            Redacted data in the same structure
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Skip sensitive keys
                if key in ['password', 'token', 'key', 'secret']:
                    result[key] = value
                    continue
                    
                # Recurse into nested objects and arrays
                if isinstance(value, (dict, list)):
                    result[key] = self._redact_json_data(value)
                elif isinstance(value, str) and len(value) > 3:  # Only redact strings with content
                    # Redact the string
                    redacted, _ = self.detector.redact_pii(value)
                    result[key] = redacted
                else:
                    result[key] = value
            return result
            
        elif isinstance(data, list):
            return [self._redact_json_data(item) for item in data]
            
        elif isinstance(data, str) and len(data) > 3:
            # Redact the string
            redacted, _ = self.detector.redact_pii(data)
            return redacted
            
        else:
            # Non-string primitive values, return as is
            return data