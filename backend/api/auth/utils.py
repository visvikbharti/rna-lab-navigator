"""
Utility functions for authentication system.
"""

import re
from typing import Optional


def get_client_ip(request) -> str:
    """
    Extract client IP address from request.
    Handles X-Forwarded-For header for proxy configurations.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Get the first IP in the chain (original client)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    
    return ip


def is_password_complex(password: str) -> bool:
    """
    Check if password meets GMP complexity requirements:
    - At least 12 characters long
    - Contains uppercase and lowercase letters
    - Contains numbers
    - Contains special characters
    - No common patterns or sequences
    """
    if len(password) < 12:
        return False
    
    # Check for required character types
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    if not all([has_upper, has_lower, has_digit, has_special]):
        return False
    
    # Check for common patterns
    common_patterns = [
        r'(.)\1{2,}',  # Same character repeated 3+ times
        r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
        r'(password|admin|user|csir|igib|rna)',  # Common words (case insensitive)
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if re.search(pattern, password_lower, re.IGNORECASE):
            return False
    
    return True


def mask_sensitive_data(data: dict, fields_to_mask: Optional[list] = None) -> dict:
    """
    Mask sensitive fields in dictionary for logging.
    """
    if fields_to_mask is None:
        fields_to_mask = [
            'password', 'token', 'refresh', 'access', 'secret',
            'api_key', 'private_key', 'session_id'
        ]
    
    masked_data = data.copy()
    
    for key, value in masked_data.items():
        if any(field in key.lower() for field in fields_to_mask):
            if isinstance(value, str) and len(value) > 4:
                masked_data[key] = f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
            else:
                masked_data[key] = '***'
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value, fields_to_mask)
    
    return masked_data


def generate_employee_id_pattern() -> str:
    """
    Generate regex pattern for valid CSIR-IGIB employee IDs.
    Format: IGIB-YYYY-XXXX (e.g., IGIB-2023-0142)
    """
    return r'^IGIB-\d{4}-\d{4}$'


def validate_employee_id(employee_id: str) -> bool:
    """
    Validate CSIR-IGIB employee ID format.
    """
    pattern = generate_employee_id_pattern()
    return bool(re.match(pattern, employee_id))


def sanitize_user_input(text: str, max_length: int = 500) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    """
    # Remove any HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove any script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Escape special characters
    escape_chars = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    }
    
    for char, escape in escape_chars.items():
        text = text.replace(char, escape)
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length] + '...'
    
    return text.strip()