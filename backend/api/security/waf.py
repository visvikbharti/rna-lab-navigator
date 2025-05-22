"""
Web Application Firewall (WAF) middleware for RNA Lab Navigator.
Implements OWASP recommended protections against common web attacks.
"""

import re
import logging
import json
from urllib.parse import parse_qs, urlparse

from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

from api.analytics.collectors import SecurityCollector

logger = logging.getLogger(__name__)


class WAFMiddleware(MiddlewareMixin):
    """
    Middleware that implements basic Web Application Firewall (WAF) functionality.
    Protects against common web attacks such as XSS, SQLi, command injection, etc.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'WAF_ENABLED', True)
        
        # Security level determines pattern sensitivity
        self.security_level = getattr(settings, 'WAF_SECURITY_LEVEL', 'medium')
        
        # Maximum violations before blocking IP
        self.max_violations = getattr(settings, 'WAF_MAX_VIOLATIONS', 3)
        
        # Block duration for repeat offenders (in seconds)
        self.block_duration = getattr(settings, 'WAF_BLOCK_IP_DURATION', 600)
        
        # Compile patterns for known attack vectors
        self.patterns = {
            'xss': self._compile_xss_patterns(),
            'sqli': self._compile_sqli_patterns(),
            'cmd_injection': self._compile_cmd_injection_patterns(),
            'path_traversal': self._compile_path_traversal_patterns(),
            'sensitive_data': self._compile_sensitive_data_patterns(),
        }
        
        # Paths to exclude from WAF checks
        self.excluded_paths = getattr(settings, 'WAF_EXCLUDED_PATHS', [
            '/admin/',  # Admin panel has its own security
            '/static/',  # Static files don't need WAF protection
            '/media/',   # Media files don't need WAF protection
            '/health/',  # Health check doesn't need WAF protection
        ])
        
        logger.info(f"WAF Middleware initialized - enabled: {self.enabled}, security level: {self.security_level}")
    
    def _compile_xss_patterns(self):
        """Compile regex patterns for XSS detection."""
        # Common patterns for all security levels
        common_patterns = [
            # Basic script tag detection
            re.compile(r'<script.*?>.*?</script.*?>', re.IGNORECASE | re.DOTALL),
            # JavaScript protocol
            re.compile(r'javascript:', re.IGNORECASE),
            # Common XSS payload patterns
            re.compile(r'document\.cookie', re.IGNORECASE),
        ]
        
        # Medium level adds more patterns
        medium_patterns = [
            # On-event handlers
            re.compile(r'on(load|error|click|mouseover|submit|keypress|change|focus|blur)=', re.IGNORECASE),
            re.compile(r'document\.location', re.IGNORECASE),
            re.compile(r'eval\s*\(', re.IGNORECASE),
            re.compile(r'alert\s*\(', re.IGNORECASE),
        ]
        
        # High level adds even more patterns
        high_patterns = [
            re.compile(r'String\.fromCharCode', re.IGNORECASE),
            re.compile(r'prompt\s*\(', re.IGNORECASE),
            re.compile(r'<img[^>]+\bonerror\b[^>]+>', re.IGNORECASE),
            re.compile(r'<iframe[^>]*>', re.IGNORECASE),
            re.compile(r'<embed[^>]*>', re.IGNORECASE),
            re.compile(r'<object[^>]*>', re.IGNORECASE),
            re.compile(r'<svg[^>]*>', re.IGNORECASE),
            re.compile(r'expression\s*\(', re.IGNORECASE),
            re.compile(r'url\s*\(', re.IGNORECASE),
            re.compile(r'@import', re.IGNORECASE),
        ]
        
        # Combine patterns based on security level
        if self.security_level == 'low':
            return common_patterns
        elif self.security_level == 'medium':
            return common_patterns + medium_patterns
        else:  # high
            return common_patterns + medium_patterns + high_patterns
    
    def _compile_sqli_patterns(self):
        """Compile regex patterns for SQL injection detection."""
        # Common patterns for all security levels
        common_patterns = [
            # SQL syntax patterns (most dangerous)
            re.compile(r'(\s|;)*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|EXEC|UNION)\s', re.IGNORECASE),
            # SQL comments
            re.compile(r'--\s', re.IGNORECASE),
            re.compile(r'/\*.*?\*/', re.IGNORECASE | re.DOTALL),
            # SQL authentication bypass
            re.compile(r"'\s*OR\s*'.*?'", re.IGNORECASE),
            re.compile(r"'\s*OR\s*[0-9]", re.IGNORECASE),
        ]
        
        # Medium level adds more patterns
        medium_patterns = [
            re.compile(r'(\s|;)*(FROM|WHERE|GROUP BY|ORDER BY|HAVING)\s', re.IGNORECASE),
            re.compile(r'#\s', re.IGNORECASE),
            re.compile(r'\bOR\b.+?[=1]', re.IGNORECASE),
            # Blind SQL injection
            re.compile(r'SLEEP\s*\(', re.IGNORECASE),
            re.compile(r'WAITFOR\s+DELAY', re.IGNORECASE),
        ]
        
        # High level adds even more patterns
        high_patterns = [
            re.compile(r'BENCHMARK\s*\(', re.IGNORECASE),
            re.compile(r'pg_sleep', re.IGNORECASE),
            re.compile(r'sys\.user_tables', re.IGNORECASE),
            re.compile(r'information_schema\.tables', re.IGNORECASE),
            re.compile(r'sysobjects', re.IGNORECASE),
            re.compile(r'CASE\s+WHEN', re.IGNORECASE),
            re.compile(r'CONVERT\s*\(', re.IGNORECASE),
            re.compile(r'CHAR\s*\(', re.IGNORECASE),
            re.compile(r'CONCAT\s*\(', re.IGNORECASE),
            re.compile(r'VARCHAR', re.IGNORECASE),
            re.compile(r'@@version', re.IGNORECASE),
        ]
        
        # Combine patterns based on security level
        if self.security_level == 'low':
            return common_patterns
        elif self.security_level == 'medium':
            return common_patterns + medium_patterns
        else:  # high
            return common_patterns + medium_patterns + high_patterns
    
    def _compile_cmd_injection_patterns(self):
        """Compile regex patterns for command injection detection."""
        # Common patterns for all security levels
        common_patterns = [
            # Unix command patterns
            re.compile(r'`.*?`'),  # Backticks for command execution
            re.compile(r'\$\(.*?\)'),  # $(command) syntax
            # Shell special chars (most dangerous)
            re.compile(r'(\||;|\$)', re.IGNORECASE),
        ]
        
        # Medium level adds more patterns
        medium_patterns = [
            re.compile(r'(>|<|\(|\))', re.IGNORECASE),  # More shell special chars
            # Common dangerous command injection payloads
            re.compile(r'\b(wget|curl|nc|netcat|telnet|ssh)\b', re.IGNORECASE),
            # Windows command patterns
            re.compile(r'\b(cmd|powershell)\b', re.IGNORECASE),
        ]
        
        # High level adds even more patterns
        high_patterns = [
            re.compile(r'&', re.IGNORECASE),  # Very common in URLs, only block at high level
            # More common Unix commands
            re.compile(r'\b(cat|grep|ls|pwd|echo|rm|cp|mv|chmod|chown|touch|find)\b', re.IGNORECASE),
            # More Windows commands
            re.compile(r'\b(start|copy|del|move|ren|dir|erase|cd)\b', re.IGNORECASE),
            # Additional dangerous commands
            re.compile(r'\b(nslookup|ifconfig|ipconfig|netstat|traceroute|gcc|python|perl|php)\b', re.IGNORECASE),
        ]
        
        # Combine patterns based on security level
        if self.security_level == 'low':
            return common_patterns
        elif self.security_level == 'medium':
            return common_patterns + medium_patterns
        else:  # high
            return common_patterns + medium_patterns + high_patterns
    
    def _compile_path_traversal_patterns(self):
        """Compile regex patterns for path traversal detection."""
        # Common patterns for all security levels
        common_patterns = [
            # Basic directory traversal patterns
            re.compile(r'\.\.(/|\\)'),  # ../
            # Common sensitive file targets
            re.compile(r'etc(/|\\)passwd', re.IGNORECASE),
        ]
        
        # Medium level adds more patterns
        medium_patterns = [
            # URL encoded traversal
            re.compile(r'\.\.(%2f|%5c)', re.IGNORECASE),  # ..%2f or ..%5c (URL encoded)
            # More sensitive files
            re.compile(r'etc(/|\\)shadow', re.IGNORECASE),
            re.compile(r'windows(/|\\)win.ini', re.IGNORECASE),
            re.compile(r'boot.ini', re.IGNORECASE),
        ]
        
        # High level adds even more patterns
        high_patterns = [
            # Double-encoded traversal
            re.compile(r'(%252e%252e)(\/|%255c)', re.IGNORECASE),
            # Additional sensitive paths
            re.compile(r'proc(/|\\)self', re.IGNORECASE),
            re.compile(r'etc(/|\\)(group|hosts|motd|issue)', re.IGNORECASE),
            re.compile(r'\.ssh(/|\\)id_rsa', re.IGNORECASE),
            re.compile(r'\.bash_history', re.IGNORECASE),
            re.compile(r'\.env', re.IGNORECASE),
            re.compile(r'config\.php', re.IGNORECASE),
            re.compile(r'wp-config\.php', re.IGNORECASE),
            re.compile(r'credentials', re.IGNORECASE),
        ]
        
        # Combine patterns based on security level
        if self.security_level == 'low':
            return common_patterns
        elif self.security_level == 'medium':
            return common_patterns + medium_patterns
        else:  # high
            return common_patterns + medium_patterns + high_patterns
    
    def _compile_sensitive_data_patterns(self):
        """Compile regex patterns for sensitive data detection."""
        # Common patterns for all security levels
        common_patterns = [
            # Passwords in URL parameters
            re.compile(r'(pass|pwd|password)[=:]', re.IGNORECASE),
            # Credit card patterns - only basic Visa format at low level
            re.compile(r'4[0-9]{12}(?:[0-9]{3})?'),  # Visa
        ]
        
        # Medium level adds more patterns
        medium_patterns = [
            # API keys and common secrets
            re.compile(r'(api|access)[_-]?(key|token|secret)', re.IGNORECASE),
            # More credit card patterns
            re.compile(r'5[1-5][0-9]{14}'),  # Mastercard
            re.compile(r'3[47][0-9]{13}'),  # American Express
            # Social security number (US)
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        ]
        
        # High level adds even more patterns
        high_patterns = [
            # More API and secret patterns
            re.compile(r'(app|account|private|secret)[_-]?(key|token|secret|password)', re.IGNORECASE),
            re.compile(r'bearer\s+[a-zA-Z0-9_\-\.]+', re.IGNORECASE),  # Bearer tokens
            # OAuth tokens
            re.compile(r'(oauth|refresh)[_-]token', re.IGNORECASE),
            # Database connection strings
            re.compile(r'(jdbc|odbc):.*', re.IGNORECASE),
            re.compile(r'(mongodb|redis|postgres)://.*', re.IGNORECASE),
            # AWS keys
            re.compile(r'AKIA[0-9A-Z]{16}'),  # AWS Access Key ID
            re.compile(r'AWS_SECRET_ACCESS_KEY', re.IGNORECASE),
            # More credit cards
            re.compile(r'6(?:011|5[0-9]{2})[0-9]{12}'),  # Discover
            re.compile(r'(?:2131|1800|35\d{3})\d{11}'),  # JCB
            # Other personal information
            re.compile(r'\b[A-Z]{2}[0-9]{7}\b'),  # Passport number
            re.compile(r'\b[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}\b'),  # UK National Insurance number
        ]
        
        # Combine patterns based on security level
        if self.security_level == 'low':
            return common_patterns
        elif self.security_level == 'medium':
            return common_patterns + medium_patterns
        else:  # high
            return common_patterns + medium_patterns + high_patterns
    
    def _check_attack_vectors(self, request_data, attack_type):
        """
        Check request data against attack patterns.
        
        Args:
            request_data: String data to check
            attack_type: Type of attack patterns to check against
            
        Returns:
            Tuple of (is_attack, matched_pattern)
        """
        if not request_data or not isinstance(request_data, str):
            return False, None
        
        for pattern in self.patterns.get(attack_type, []):
            match = pattern.search(request_data)
            if match:
                return True, match.group(0)
        
        return False, None
    
    def _get_request_data(self, request):
        """
        Extract data from request for inspection.
        
        Args:
            request: The HTTP request
            
        Returns:
            Dictionary of data extracted from the request
        """
        data = {}
        
        # Headers (excluding common non-suspicious headers)
        excluded_headers = ['CONTENT_LENGTH', 'CONTENT_TYPE', 'HTTP_ACCEPT',
                           'HTTP_ACCEPT_ENCODING', 'HTTP_ACCEPT_LANGUAGE',
                           'HTTP_HOST', 'HTTP_USER_AGENT', 'HTTP_CONNECTION']
        
        headers = {k.lower(): v for k, v in request.META.items()
                 if k.startswith('HTTP_') and k not in excluded_headers}
        data['headers'] = headers
        
        # Query string
        query_string = request.META.get('QUERY_STRING', '')
        if query_string:
            parsed_url = urlparse(request.build_absolute_uri())
            data['query'] = parse_qs(parsed_url.query)
        
        # POST data (if applicable)
        if request.method == 'POST':
            if hasattr(request, 'body') and request.body:
                try:
                    # Try to parse as JSON
                    if request.content_type == 'application/json':
                        body_data = json.loads(request.body.decode('utf-8'))
                        data['body'] = body_data
                    else:
                        # For form data
                        data['body'] = request.POST.dict()
                except (ValueError, UnicodeDecodeError):
                    # If can't parse as JSON, just use the raw body
                    data['body'] = request.body.decode('utf-8', errors='ignore')
        
        return data
    
    def _scan_request_data(self, request_data):
        """
        Scan request data for attack patterns.
        
        Args:
            request_data: Dictionary of request data
            
        Returns:
            Tuple of (is_attack, attack_type, matched_pattern)
        """
        # Check headers
        for header, value in request_data.get('headers', {}).items():
            for attack_type in self.patterns.keys():
                is_attack, pattern = self._check_attack_vectors(value, attack_type)
                if is_attack:
                    return True, attack_type, pattern
        
        # Check query parameters
        for param, values in request_data.get('query', {}).items():
            for value in values:
                for attack_type in self.patterns.keys():
                    is_attack, pattern = self._check_attack_vectors(value, attack_type)
                    if is_attack:
                        return True, attack_type, pattern
        
        # Check body data
        body = request_data.get('body')
        if body:
            if isinstance(body, dict):
                # For JSON/form data, check each value
                for key, value in body.items():
                    if isinstance(value, str):
                        for attack_type in self.patterns.keys():
                            is_attack, pattern = self._check_attack_vectors(value, attack_type)
                            if is_attack:
                                return True, attack_type, pattern
            elif isinstance(body, str):
                # For raw body data
                for attack_type in self.patterns.keys():
                    is_attack, pattern = self._check_attack_vectors(body, attack_type)
                    if is_attack:
                        return True, attack_type, pattern
        
        return False, None, None
    
    def _is_ip_blocked(self, ip_address):
        """
        Check if an IP address is blocked due to repeated violations.
        
        Args:
            ip_address: The IP address to check
            
        Returns:
            Boolean indicating if the IP is blocked
        """
        block_key = f"waf:ip_block:{ip_address}"
        return cache.get(block_key, False)
    
    def _increment_violation_count(self, ip_address):
        """
        Increment the violation count for an IP address.
        If count exceeds maximum, block the IP.
        
        Args:
            ip_address: The IP address of the violator
            
        Returns:
            Tuple of (count, is_now_blocked)
        """
        count_key = f"waf:violation_count:{ip_address}"
        block_key = f"waf:ip_block:{ip_address}"
        
        # Get current count (or 0 if not found)
        count = cache.get(count_key, 0)
        
        # Increment count
        count += 1
        
        # Set TTL to 24 hours for violation count
        cache.set(count_key, count, 86400)  # 24 hours
        
        # Check if count exceeds maximum
        if count >= self.max_violations:
            # Block the IP for the configured duration
            cache.set(block_key, True, self.block_duration)
            
            # Log the blocking
            logger.warning(f"WAF blocked IP {ip_address} for {self.block_duration} seconds "
                         f"due to {count} violations in 24 hours")
            
            return count, True
        
        return count, False
    
    def process_request(self, request):
        """
        Process the request before it reaches the view.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse if attack is detected or IP is blocked, None otherwise
        """
        if not self.enabled:
            return None
        
        # Get client IP address
        ip_address = request.META.get('REMOTE_ADDR', '')
        
        # Check if IP is already blocked
        if self._is_ip_blocked(ip_address):
            logger.info(f"WAF blocked request from previously blocked IP: {ip_address}")
            return JsonResponse({
                'error': 'Access denied',
                'detail': 'Your IP address has been temporarily blocked due to security violations',
            }, status=403)
        
        # Check if view is WAF-exempt
        if hasattr(request, 'resolver_match') and request.resolver_match:
            callback = request.resolver_match.func
            if getattr(callback, 'waf_exempt', False):
                return None
        
        # Skip WAF checks for excluded paths
        path = request.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return None
        
        # Extract request data
        request_data = self._get_request_data(request)
        
        # Scan request data for attack patterns
        is_attack, attack_type, pattern = self._scan_request_data(request_data)
        if is_attack:
            # Increment violation count and check if IP should be blocked
            count, is_now_blocked = self._increment_violation_count(ip_address)
            
            # Log the attack
            if is_now_blocked:
                logger.warning(f"WAF blocked {attack_type} attack from {ip_address} "
                             f"to {request.path} - Pattern: {pattern} - "
                             f"IP has been blocked after {count} violations")
            else:
                logger.warning(f"WAF blocked {attack_type} attack from {ip_address} "
                             f"to {request.path} - Pattern: {pattern} - "
                             f"Violation {count} of {self.max_violations}")
            
            # Record security event
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            else:
                user = None
                
            SecurityCollector.record_security_event(
                event_type="suspicious_activity",
                description=f"WAF blocked {attack_type} attack" + 
                            (f" and blocked IP for {self.block_duration} seconds" if is_now_blocked else ""),
                user=user,
                ip_address=ip_address,
                severity="error",
                details={
                    'path': request.path,
                    'method': request.method,
                    'attack_type': attack_type,
                    'pattern': pattern,
                    'violation_count': count,
                    'ip_blocked': is_now_blocked,
                }
            )
            
            # Block the request with a 403 Forbidden response
            block_message = "Security violation detected"
            if is_now_blocked:
                block_message = f"Security violation detected. Your IP has been blocked for {self.block_duration/60} minutes due to repeated violations."
            
            return JsonResponse({
                'error': 'Request blocked',
                'detail': block_message,
            }, status=403)
        
        return None


def waf_exempt(view_func):
    """
    Decorator to exempt a view from WAF protection.
    
    Args:
        view_func: The view function to exempt
        
    Returns:
        The decorated view function
    """
    view_func.waf_exempt = True
    return view_func