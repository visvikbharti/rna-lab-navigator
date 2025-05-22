#!/usr/bin/env python
"""
Clear WAF blocks script for RNA Lab Navigator

This script connects to the Redis cache used by Django and clears
any IP blocks that have been set by the Web Application Firewall (WAF).
"""

import os
import sys
import django
from django.core.cache import cache
import redis

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")
django.setup()

def clear_waf_blocks():
    """
    Clear all WAF blocks from the cache
    """
    # Get all keys with the waf prefix
    from django.conf import settings
    
    # Get Redis connection settings from Django
    redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
    
    # Connect to Redis
    r = redis.from_url(redis_url)
    
    # Find all WAF-related keys
    waf_keys = r.keys('waf:*')
    
    if not waf_keys:
        print("No WAF blocks found in cache.")
        return
    
    # Delete all WAF keys
    count = 0
    for key in waf_keys:
        r.delete(key)
        count += 1
        print(f"Deleted key: {key.decode('utf-8')}")
    
    print(f"Cleared {count} WAF blocks from cache.")

if __name__ == "__main__":
    clear_waf_blocks()