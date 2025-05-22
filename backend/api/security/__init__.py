"""
Security module for RNA Lab Navigator.
This module includes PII detection, request filtering, differential privacy,
connection security, verification, and other security-related utilities.
"""

# Import key components for easy access
from .pii_detector import PIIDetector, get_detector
from .middleware import PIIFilterMiddleware
from .headers import SecurityHeadersMiddleware, SecurityHeadersReporter
from .connection import ConnectionTimeoutMiddleware, get_or_create_tracker
from .differential_privacy import protect_embedding, protect_embedding_deterministic, get_embedding_protector
from .verification import SecurityVerifier, get_verifier
from .error_handling import (
    SecurityError, AuthenticationError, AuthorizationError, PIIDetectionError,
    DifferentialPrivacyError, SecurityConfigurationError, ConnectionSecurityError,
    handle_security_error, security_error_to_response, security_exception_handler,
    log_security_event, add_secure_headers
)