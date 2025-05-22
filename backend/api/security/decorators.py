"""
Security-related decorators for the RNA Lab Navigator.
"""

from functools import wraps
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


def waf_exempt(view_func):
    """
    Decorator to exempt a view from WAF protection.
    Use this for views that may legitimately contain patterns that trigger WAF rules,
    such as code snippets, markdown with script examples, etc.
    
    Args:
        view_func: The view function to exempt
        
    Returns:
        The decorated view function
    """
    view_func.waf_exempt = True
    return view_func


def class_waf_exempt(cls):
    """
    Class decorator to exempt all methods of a class-based view from WAF protection.
    
    Args:
        cls: The class to exempt
        
    Returns:
        The decorated class
    """
    dispatch = cls.dispatch
    
    @wraps(dispatch)
    def waf_exempt_dispatch(self, *args, **kwargs):
        return dispatch(self, *args, **kwargs)
    
    waf_exempt_dispatch.waf_exempt = True
    cls.dispatch = waf_exempt_dispatch
    return cls


def rate_limit_exempt(view_func):
    """
    Decorator to exempt a view from rate limiting.
    Use this for internal API calls or health check endpoints that should not be rate limited.
    
    Args:
        view_func: The view function to exempt
        
    Returns:
        The decorated view function
    """
    view_func.rate_limit_exempt = True
    return view_func


def secure_api_view(csrf_protected=True, rate_limit=True, waf_protected=True):
    """
    Decorator that applies multiple security measures to a view.
    
    Args:
        csrf_protected: Whether to apply CSRF protection
        rate_limit: Whether to apply rate limiting
        waf_protected: Whether to apply WAF protection
        
    Returns:
        Decorator function that applies the specified security measures
    """
    def decorator(view_func):
        # Apply CSRF protection (or not)
        if not csrf_protected:
            view_func = csrf_exempt(view_func)
        
        # Apply rate limiting (or not)
        if not rate_limit:
            view_func.rate_limit_exempt = True
        
        # Apply WAF protection (or not)
        if not waf_protected:
            view_func.waf_exempt = True
        
        return view_func
    
    return decorator