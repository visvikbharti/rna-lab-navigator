"""
Security verification system for RNA Lab Navigator.
Provides a comprehensive security checking framework to validate
the implementation of security measures throughout the system.
"""

import os
import logging
import json
import re
import time
import ssl
import socket
import threading
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.test.client import Client
from django.http import HttpRequest

from .headers import SecurityHeadersReporter
from .connection import get_or_create_tracker, ConnectionTracker
from .pii_detector import get_detector

logger = logging.getLogger(__name__)


class SecurityVerifier:
    """
    Comprehensive security verification framework for RNA Lab Navigator.
    Checks configuration, code, and runtime security measures.
    """
    
    def __init__(self):
        """Initialize the security verifier"""
        self.checks = []
        self.results = {}
        self.overall_status = "Unknown"
        
        # Register all security checks
        self._register_checks()
        
    def _register_checks(self):
        """Register all security checks"""
        # Configuration checks
        self.checks.extend([
            self.check_debug_mode,
            self.check_secret_key,
            self.check_allowed_hosts,
            self.check_secure_cookies,
            self.check_security_middleware,
            self.check_pii_settings,
        ])
        
        # Runtime checks
        self.checks.extend([
            self.check_security_headers,
            self.check_csp_header,
            self.check_connection_timeout,
            self.check_dp_embedding_protection,
            self.check_ssl_configuration,
        ])
        
        # Database and storage checks
        self.checks.extend([
            self.check_database_connections,
            self.check_media_permissions,
        ])
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all security checks and return results.
        
        Returns:
            Dict with check results and overall status
        """
        results = {}
        
        # Run each check
        for check in self.checks:
            check_name = check.__name__
            try:
                result = check()
                results[check_name] = result
            except Exception as e:
                logger.error(f"Error in check {check_name}: {e}")
                results[check_name] = {
                    "status": "error",
                    "message": f"Check failed with error: {str(e)}",
                    "details": None,
                }
                
        # Calculate overall status
        statuses = [r.get("status") for r in results.values()]
        if "critical" in statuses:
            overall_status = "critical"
        elif "warning" in statuses:
            overall_status = "warning"
        elif "error" in statuses:
            overall_status = "error"
        elif all(s == "pass" for s in statuses):
            overall_status = "pass"
        else:
            overall_status = "partial"
            
        # Store results
        self.results = results
        self.overall_status = overall_status
        
        # Return results
        return {
            "checks": results,
            "overall_status": overall_status,
            "timestamp": time.time(),
        }
    
    # === Configuration Checks ===
    
    def check_debug_mode(self) -> Dict[str, Any]:
        """Check if DEBUG mode is disabled in production"""
        is_debug = getattr(settings, "DEBUG", False)
        
        if is_debug:
            return {
                "status": "critical",
                "message": "DEBUG mode is enabled. This should be disabled in production.",
                "details": {
                    "current_setting": is_debug,
                },
            }
        else:
            return {
                "status": "pass",
                "message": "DEBUG mode is disabled.",
                "details": None,
            }
    
    def check_secret_key(self) -> Dict[str, Any]:
        """Check if SECRET_KEY is properly set and not default"""
        secret_key = getattr(settings, "SECRET_KEY", "")
        
        # Check if using the default key from settings.py
        is_default = secret_key == "django-insecure-key-for-development-only"
        
        # Check if too short
        is_too_short = len(secret_key) < 32
        
        # Check if likely a placeholder
        is_placeholder = any(s in secret_key.lower() for s in ["insecure", "change", "default", "placeholder"])
        
        if is_default or is_placeholder:
            return {
                "status": "critical",
                "message": "Using default or placeholder SECRET_KEY. This must be changed in production.",
                "details": {
                    "is_default": is_default,
                    "is_placeholder": is_placeholder,
                },
            }
        elif is_too_short:
            return {
                "status": "warning",
                "message": "SECRET_KEY is too short. It should be at least 32 characters.",
                "details": {
                    "length": len(secret_key),
                },
            }
        else:
            return {
                "status": "pass",
                "message": "SECRET_KEY is properly set.",
                "details": None,
            }
    
    def check_allowed_hosts(self) -> Dict[str, Any]:
        """Check if ALLOWED_HOSTS is properly configured"""
        allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])
        
        # Check if using wildcard
        has_wildcard = "*" in allowed_hosts
        
        # Check if localhost only
        localhost_only = all(host in ["localhost", "127.0.0.1"] for host in allowed_hosts)
        
        # For production, check domain specificity
        is_prod = not getattr(settings, "DEBUG", False)
        lacks_specific_domains = is_prod and (not allowed_hosts or localhost_only)
        
        if has_wildcard:
            return {
                "status": "warning",
                "message": "ALLOWED_HOSTS contains a wildcard (*), which is too permissive.",
                "details": {
                    "current_setting": allowed_hosts,
                },
            }
        elif lacks_specific_domains:
            return {
                "status": "warning",
                "message": "ALLOWED_HOSTS should include specific domains in production.",
                "details": {
                    "current_setting": allowed_hosts,
                },
            }
        else:
            return {
                "status": "pass",
                "message": "ALLOWED_HOSTS is properly configured.",
                "details": {
                    "current_setting": allowed_hosts,
                },
            }
    
    def check_secure_cookies(self) -> Dict[str, Any]:
        """Check if secure cookie settings are enabled"""
        session_cookie_secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
        csrf_cookie_secure = getattr(settings, "CSRF_COOKIE_SECURE", False)
        session_cookie_httponly = getattr(settings, "SESSION_COOKIE_HTTPONLY", False)
        
        # Allow non-secure cookies in debug mode
        is_debug = getattr(settings, "DEBUG", False)
        if is_debug:
            if session_cookie_secure and csrf_cookie_secure:
                return {
                    "status": "pass",
                    "message": "Secure cookie settings are enabled, even in DEBUG mode.",
                    "details": None,
                }
            else:
                return {
                    "status": "pass",
                    "message": "Insecure cookies acceptable in DEBUG mode.",
                    "details": {
                        "session_cookie_secure": session_cookie_secure,
                        "csrf_cookie_secure": csrf_cookie_secure,
                        "session_cookie_httponly": session_cookie_httponly,
                    },
                }
        
        # Check for secure cookies in production
        if not session_cookie_secure or not csrf_cookie_secure:
            return {
                "status": "warning",
                "message": "Secure cookie settings are not fully enabled. This may allow session hijacking.",
                "details": {
                    "session_cookie_secure": session_cookie_secure,
                    "csrf_cookie_secure": csrf_cookie_secure,
                    "session_cookie_httponly": session_cookie_httponly,
                },
            }
        elif not session_cookie_httponly:
            return {
                "status": "warning",
                "message": "SESSION_COOKIE_HTTPONLY is not enabled. This may allow XSS attacks.",
                "details": {
                    "session_cookie_secure": session_cookie_secure,
                    "csrf_cookie_secure": csrf_cookie_secure,
                    "session_cookie_httponly": session_cookie_httponly,
                },
            }
        else:
            return {
                "status": "pass",
                "message": "Secure cookie settings are enabled.",
                "details": None,
            }
    
    def check_security_middleware(self) -> Dict[str, Any]:
        """Check if required security middleware is enabled"""
        middleware = getattr(settings, "MIDDLEWARE", [])
        
        # Required middleware
        required_middleware = [
            "django.middleware.security.SecurityMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "api.security.headers.SecurityHeadersMiddleware",
            "api.security.middleware.PIIFilterMiddleware",
        ]
        
        # Check which required middleware is missing
        missing = [m for m in required_middleware if m not in middleware]
        
        if missing:
            return {
                "status": "warning",
                "message": "Some security middleware is missing.",
                "details": {
                    "missing_middleware": missing,
                },
            }
        else:
            return {
                "status": "pass",
                "message": "All required security middleware is enabled.",
                "details": None,
            }
    
    def check_pii_settings(self) -> Dict[str, Any]:
        """Check if PII detection settings are properly configured"""
        scan_requests = getattr(settings, "SCAN_REQUESTS_FOR_PII", False)
        
        if not scan_requests:
            return {
                "status": "warning",
                "message": "PII request scanning is disabled. Consider enabling for sensitive data.",
                "details": {
                    "SCAN_REQUESTS_FOR_PII": scan_requests,
                },
            }
        else:
            return {
                "status": "pass",
                "message": "PII detection settings are properly configured.",
                "details": {
                    "SCAN_REQUESTS_FOR_PII": scan_requests,
                },
            }
    
    # === Runtime Checks ===
    
    def check_security_headers(self) -> Dict[str, Any]:
        """Check if security headers are properly configured"""
        # Create a test client
        client = Client()
        
        # Make a request to a simple URL
        response = client.get("/api/health/", secure=True)
        
        # Check security headers
        headers = response.headers
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
        ]
        
        missing = [h for h in required_headers if h not in headers]
        
        if missing:
            return {
                "status": "warning",
                "message": "Some security headers are missing.",
                "details": {
                    "missing_headers": missing,
                    "present_headers": list(headers.keys()),
                },
            }
        else:
            return {
                "status": "pass",
                "message": "All required security headers are present.",
                "details": {
                    "headers": {k: v for k, v in headers.items() if k in required_headers},
                },
            }
    
    def check_csp_header(self) -> Dict[str, Any]:
        """Check if Content-Security-Policy header is properly configured"""
        # Create a test client
        client = Client()
        
        # Make a request to a simple URL
        response = client.get("/api/health/", secure=True)
        
        # Check CSP header
        headers = response.headers
        csp_header = headers.get("Content-Security-Policy")
        
        if not csp_header:
            return {
                "status": "warning",
                "message": "Content-Security-Policy header is missing.",
                "details": None,
            }
        
        # Check for unsafe directives
        has_unsafe_inline = "'unsafe-inline'" in csp_header
        has_unsafe_eval = "'unsafe-eval'" in csp_header
        
        if has_unsafe_inline and has_unsafe_eval:
            return {
                "status": "warning",
                "message": "CSP header contains both 'unsafe-inline' and 'unsafe-eval' directives.",
                "details": {
                    "csp_header": csp_header,
                },
            }
        elif has_unsafe_inline or has_unsafe_eval:
            return {
                "status": "pass",
                "message": "CSP header contains some unsafe directives, but this may be necessary for the application.",
                "details": {
                    "csp_header": csp_header,
                    "has_unsafe_inline": has_unsafe_inline,
                    "has_unsafe_eval": has_unsafe_eval,
                },
            }
        else:
            return {
                "status": "pass",
                "message": "Content-Security-Policy header is properly configured.",
                "details": {
                    "csp_header": csp_header,
                },
            }
    
    def check_connection_timeout(self) -> Dict[str, Any]:
        """Check if connection timeout is enabled and working"""
        enable_timeout = getattr(settings, "ENABLE_CONNECTION_TIMEOUT", False)
        timeout_seconds = getattr(settings, "CONNECTION_TIMEOUT_SECONDS", 1800)
        
        if not enable_timeout:
            return {
                "status": "warning",
                "message": "Connection timeout is disabled. Consider enabling for security.",
                "details": None,
            }
        
        # Create a test connection tracker
        tracker = ConnectionTracker("test_session", timeout_seconds)
        
        # Check if timeout works
        tracker.last_activity = time.time() - (timeout_seconds + 10)
        is_timeout = tracker.check_timeout()
        
        if not is_timeout:
            return {
                "status": "warning",
                "message": "Connection timeout is not working correctly.",
                "details": {
                    "timeout_seconds": timeout_seconds,
                },
            }
        else:
            return {
                "status": "pass",
                "message": "Connection timeout is enabled and working.",
                "details": {
                    "timeout_seconds": timeout_seconds,
                },
            }
    
    def check_dp_embedding_protection(self) -> Dict[str, Any]:
        """Check if differential privacy for embeddings is enabled"""
        enable_dp = getattr(settings, "ENABLE_DP_EMBEDDING_PROTECTION", False)
        
        if not enable_dp:
            return {
                "status": "warning",
                "message": "Differential privacy for embeddings is disabled. Consider enabling for sensitive data.",
                "details": None,
            }
        else:
            return {
                "status": "pass",
                "message": "Differential privacy for embeddings is enabled.",
                "details": {
                    "epsilon": getattr(settings, "DP_EPSILON", 0.1),
                    "sensitivity": getattr(settings, "DP_SENSITIVITY", 0.1),
                },
            }
    
    def check_ssl_configuration(self) -> Dict[str, Any]:
        """Check if SSL/TLS configuration is secure"""
        # This is primarily relevant for production
        is_debug = getattr(settings, "DEBUG", False)
        
        if is_debug:
            return {
                "status": "pass",
                "message": "SSL check skipped in DEBUG mode.",
                "details": None,
            }
        
        # Try to get the hostname from ALLOWED_HOSTS or SITE_URL
        allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])
        site_url = getattr(settings, "SITE_URL", "")
        
        hostname = None
        if site_url:
            parsed_url = urlparse(site_url)
            hostname = parsed_url.netloc
        elif allowed_hosts and allowed_hosts[0] not in ["localhost", "127.0.0.1", "*"]:
            hostname = allowed_hosts[0]
        
        if not hostname:
            return {
                "status": "warning",
                "message": "Could not determine hostname for SSL check.",
                "details": None,
            }
        
        # Try to connect to the hostname with TLS
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check if certificate is valid
                    if not cert:
                        return {
                            "status": "critical",
                            "message": f"No SSL certificate found for {hostname}.",
                            "details": None,
                        }
                    
                    # Check if certificate is expired
                    import datetime
                    expires = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                    now = datetime.datetime.now()
                    
                    days_left = (expires - now).days
                    
                    if days_left < 0:
                        return {
                            "status": "critical",
                            "message": f"SSL certificate for {hostname} is expired.",
                            "details": {
                                "expires": expires.isoformat(),
                            },
                        }
                    elif days_left < 30:
                        return {
                            "status": "warning",
                            "message": f"SSL certificate for {hostname} expires soon ({days_left} days).",
                            "details": {
                                "expires": expires.isoformat(),
                                "days_left": days_left,
                            },
                        }
                    else:
                        return {
                            "status": "pass",
                            "message": f"SSL certificate for {hostname} is valid.",
                            "details": {
                                "expires": expires.isoformat(),
                                "days_left": days_left,
                            },
                        }
        except Exception as e:
            logger.error(f"Error checking SSL for {hostname}: {e}")
            return {
                "status": "error",
                "message": f"Could not check SSL for {hostname}: {str(e)}",
                "details": None,
            }
    
    # === Database and Storage Checks ===
    
    def check_database_connections(self) -> Dict[str, Any]:
        """Check if database connections are secure"""
        try:
            # Get database configuration
            databases = getattr(settings, "DATABASES", {})
            default_db = databases.get("default", {})
            
            # Check for SSL
            ssl_mode = default_db.get("OPTIONS", {}).get("sslmode")
            host = default_db.get("HOST", "")
            
            # If using non-local DB without SSL
            if host and host not in ["localhost", "127.0.0.1"] and ssl_mode not in ["require", "verify-ca", "verify-full"]:
                return {
                    "status": "warning",
                    "message": "Database connection is not using SSL/TLS. This may allow eavesdropping.",
                    "details": {
                        "host": host,
                        "sslmode": ssl_mode,
                    },
                }
            else:
                return {
                    "status": "pass",
                    "message": "Database connections are secure.",
                    "details": None,
                }
        except Exception as e:
            logger.error(f"Error checking database connections: {e}")
            return {
                "status": "error",
                "message": f"Could not check database connections: {str(e)}",
                "details": None,
            }
    
    def check_media_permissions(self) -> Dict[str, Any]:
        """Check if media directory has appropriate permissions"""
        media_root = getattr(settings, "MEDIA_ROOT", "")
        
        if not media_root or not os.path.exists(media_root):
            return {
                "status": "warning",
                "message": "MEDIA_ROOT does not exist.",
                "details": {
                    "media_root": media_root,
                },
            }
        
        try:
            # Check if media directory is writable
            is_writable = os.access(media_root, os.W_OK)
            
            # Check if media directory has appropriate permissions
            # On Unix, check for 0o755 or 0o750
            try:
                permissions = oct(os.stat(media_root).st_mode & 0o777)
                is_secure = permissions in ["0o755", "0o750", "0o700"]
            except:
                # Windows doesn't have the same permission model
                is_secure = True
                permissions = "N/A (Windows)"
            
            if not is_writable:
                return {
                    "status": "warning",
                    "message": "MEDIA_ROOT is not writable. This may cause file upload failures.",
                    "details": {
                        "media_root": media_root,
                        "permissions": permissions,
                    },
                }
            elif not is_secure:
                return {
                    "status": "warning",
                    "message": "MEDIA_ROOT has overly permissive permissions.",
                    "details": {
                        "media_root": media_root,
                        "permissions": permissions,
                    },
                }
            else:
                return {
                    "status": "pass",
                    "message": "MEDIA_ROOT has appropriate permissions.",
                    "details": {
                        "media_root": media_root,
                        "permissions": permissions,
                    },
                }
        except Exception as e:
            logger.error(f"Error checking media permissions: {e}")
            return {
                "status": "error",
                "message": f"Could not check media permissions: {str(e)}",
                "details": None,
            }
    
    def generate_report(self, include_details: bool = True) -> Dict[str, Any]:
        """
        Generate a comprehensive security report.
        
        Args:
            include_details: Whether to include detailed check results
            
        Returns:
            Dict with report data
        """
        # Run all checks
        self.run_all_checks()
        
        # Build report
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": self.overall_status,
            "summary": self._generate_summary(),
        }
        
        # Add check results
        if include_details:
            report["checks"] = self.results
            
        # Add recommendations
        report["recommendations"] = self._generate_recommendations()
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of check results"""
        # Count results by status
        status_counts = {}
        for result in self.results.values():
            status = result.get("status")
            status_counts[status] = status_counts.get(status, 0) + 1
            
        # Calculate percentage of passing checks
        total_checks = len(self.results)
        passing_checks = status_counts.get("pass", 0)
        passing_percent = (passing_checks / total_checks) * 100 if total_checks > 0 else 0
        
        return {
            "total_checks": total_checks,
            "passing_checks": passing_checks,
            "passing_percent": passing_percent,
            "status_counts": status_counts,
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on check results"""
        recommendations = []
        
        # Add recommendations for non-passing checks
        for check_name, result in self.results.items():
            if result.get("status") != "pass":
                # Format the check name for readability
                readable_name = " ".join(check_name.replace("check_", "").split("_")).capitalize()
                recommendations.append(f"Fix {readable_name}: {result.get('message')}")
                
        return recommendations


# Singleton instance for easy access
_default_verifier = None

def get_verifier() -> SecurityVerifier:
    """Get the default security verifier instance"""
    global _default_verifier
    if _default_verifier is None:
        _default_verifier = SecurityVerifier()
    return _default_verifier