"""
Security headers utilities for RNA Lab Navigator.
Implements security headers middleware and monitoring for HTTP security headers.
"""

import logging
import json
import requests
from typing import Dict, List, Optional, Any
from django.http import HttpRequest, HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

# Security header configuration
RECOMMENDED_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store, max-age=0",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}

# Content-Security-Policy header configuration
CSP_CONFIG = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:"],
    "script-src": ["'self'", "'unsafe-inline'"],  # Unsafe-inline needed for React in dev
    "style-src": ["'self'", "'unsafe-inline'"],  # Unsafe-inline needed for React
    "connect-src": ["'self'"],
    "font-src": ["'self'"],
    "frame-src": ["'none'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
}


class SecurityHeadersMiddleware:
    """
    Middleware that adds security headers to HTTP responses.
    Helps protect against common web vulnerabilities.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Get response from the view
        response = self.get_response(request)
        
        # Skip if response doesn't support headers
        if not hasattr(response, 'headers'):
            return response
            
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Add standard security headers
        for header, value in RECOMMENDED_SECURITY_HEADERS.items():
            response[header] = value
            
        # Add Content-Security-Policy header
        csp_header = self._build_csp_header()
        response["Content-Security-Policy"] = csp_header
        
        # Add Strict-Transport-Security header in production
        if not settings.DEBUG:
            response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    def _build_csp_header(self) -> str:
        """Build Content-Security-Policy header value"""
        # Override with settings if available
        csp_config = getattr(settings, 'CSP_CONFIG', CSP_CONFIG)
        
        # Build CSP header string
        csp_parts = []
        for directive, sources in csp_config.items():
            csp_parts.append(f"{directive} {' '.join(sources)}")
            
        return "; ".join(csp_parts)


class SecurityHeadersReporter:
    """
    Utility class to check and report on security headers.
    Can be used to monitor security posture over time.
    """
    
    def __init__(self, site_url: Optional[str] = None):
        """Initialize the security headers reporter"""
        self.site_url = site_url or settings.SITE_URL
        
    def check_headers(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Check security headers for a URL.
        
        Args:
            url: URL to check (defaults to site_url)
            
        Returns:
            Dict with security header check results
        """
        check_url = url or self.site_url
        
        try:
            # Make request with custom user agent
            headers = {
                "User-Agent": "RNA-Lab-Navigator-Security-Check/1.0"
            }
            response = requests.get(check_url, headers=headers, timeout=10, verify=True)
            
            # Extract headers
            headers = dict(response.headers)
            
            # Check for required security headers
            missing_headers = []
            for header in RECOMMENDED_SECURITY_HEADERS:
                if header not in headers:
                    missing_headers.append(header)
                    
            # Check for Strict-Transport-Security
            has_hsts = "Strict-Transport-Security" in headers
            
            # Parse CSP header if present
            csp_header = headers.get("Content-Security-Policy", "")
            csp_directives = self._parse_csp_header(csp_header)
            
            # Check for unsafe CSP directives
            unsafe_csp = []
            if csp_directives:
                for directive, sources in csp_directives.items():
                    for source in sources:
                        if source == "'unsafe-inline'" and directive in ["script-src", "style-src"]:
                            unsafe_csp.append(f"{directive}: {source}")
                        elif source == "'unsafe-eval'" and directive == "script-src":
                            unsafe_csp.append(f"{directive}: {source}")
                            
            # Calculate security score
            score = self._calculate_security_score(headers)
            
            return {
                "url": check_url,
                "status_code": response.status_code,
                "headers": headers,
                "missing_headers": missing_headers,
                "has_hsts": has_hsts,
                "csp_directives": csp_directives,
                "unsafe_csp": unsafe_csp,
                "security_score": score,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error checking security headers: {e}")
            return {
                "url": check_url,
                "error": str(e),
                "success": False
            }
    
    def _parse_csp_header(self, csp_header: str) -> Dict[str, List[str]]:
        """Parse Content-Security-Policy header value"""
        if not csp_header:
            return {}
            
        csp_directives = {}
        
        # Split by semicolons
        directives = csp_header.split(";")
        
        for directive in directives:
            directive = directive.strip()
            if not directive:
                continue
                
            # Split by first space
            parts = directive.split(" ", 1)
            if len(parts) != 2:
                continue
                
            name, sources = parts
            sources = [s.strip() for s in sources.split(" ") if s.strip()]
            csp_directives[name.strip()] = sources
            
        return csp_directives
    
    def _calculate_security_score(self, headers: Dict[str, str]) -> int:
        """
        Calculate security score based on headers.
        Score range: 0-100
        """
        score = 0
        
        # Basic security headers (50 points max)
        for header in RECOMMENDED_SECURITY_HEADERS:
            if header in headers:
                score += 5
                
        # HSTS header (10 points)
        if "Strict-Transport-Security" in headers:
            score += 10
            
        # CSP header (20 points max)
        if "Content-Security-Policy" in headers:
            csp_header = headers["Content-Security-Policy"]
            csp_directives = self._parse_csp_header(csp_header)
            
            # Check for key CSP directives
            key_directives = ["default-src", "script-src", "object-src", "base-uri"]
            for directive in key_directives:
                if directive in csp_directives:
                    score += 3
                    
            # Check for unsafe directives
            has_unsafe = False
            for directive, sources in csp_directives.items():
                for source in sources:
                    if source in ["'unsafe-inline'", "'unsafe-eval'"]:
                        has_unsafe = True
                        break
                        
            if not has_unsafe:
                score += 8
                
        # Other modern security headers (20 points max)
        modern_headers = [
            "Permissions-Policy",
            "Cross-Origin-Embedder-Policy",
            "Cross-Origin-Opener-Policy",
            "Cross-Origin-Resource-Policy"
        ]
        
        for header in modern_headers:
            if header in headers:
                score += 5
                
        return score
    
    def run_observatory_scan(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Run Mozilla Observatory scan on URL.
        
        Args:
            url: URL to scan (defaults to site_url)
            
        Returns:
            Dict with scan results
        """
        check_url = url or self.site_url
        
        try:
            # Start scan
            scan_url = "https://http-observatory.security.mozilla.org/api/v1/analyze"
            payload = {
                "host": check_url.replace("https://", "").replace("http://", "").split("/")[0],
                "hidden": "true",
                "rescan": "true"
            }
            
            response = requests.post(scan_url, data=payload, timeout=30)
            scan_data = response.json()
            
            if "scan_id" not in scan_data:
                return {
                    "url": check_url,
                    "error": "Failed to start scan",
                    "success": False
                }
                
            scan_id = scan_data["scan_id"]
            
            # Poll for results
            import time
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(5)
                
                results_url = f"https://http-observatory.security.mozilla.org/api/v1/analyze?scan={scan_id}"
                response = requests.get(results_url, timeout=30)
                results = response.json()
                
                if results.get("state") == "FINISHED":
                    return {
                        "url": check_url,
                        "observatory_score": results.get("score", 0),
                        "observatory_grade": results.get("grade", "F"),
                        "tests": results.get("tests", {}),
                        "success": True
                    }
                    
            return {
                "url": check_url,
                "error": "Scan timed out",
                "success": False
            }
        except Exception as e:
            logger.error(f"Error running Observatory scan: {e}")
            return {
                "url": check_url,
                "error": str(e),
                "success": False
            }
    
    def generate_report(self, include_observatory: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive security headers report.
        
        Args:
            include_observatory: Whether to include Mozilla Observatory scan
            
        Returns:
            Dict with report data
        """
        report = {
            "timestamp": self._get_timestamp(),
            "site_url": self.site_url,
            "header_check": self.check_headers()
        }
        
        if include_observatory:
            report["observatory"] = self.run_observatory_scan()
            
        return report
    
    def _get_timestamp(self) -> str:
        """Get ISO format timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()