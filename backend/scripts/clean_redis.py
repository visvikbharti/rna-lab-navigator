#!/usr/bin/env python
"""
Redis Cleaning Script for RNA Lab Navigator
This script connects to Redis and flushes all keys related to WAF blocking,
rate limiting, and other cached data to troubleshoot connectivity issues.
"""

import redis
import os
import sys
import django
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.append(project_dir)
sys.path.append(os.path.join(project_dir, 'backend'))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")
django.setup()

from django.conf import settings

def flush_redis():
    """
    Connect to Redis and flush all data.
    """
    redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
    
    try:
        # Connect to Redis
        r = redis.from_url(redis_url)
        
        # Check connection
        ping_response = r.ping()
        if ping_response:
            logger.info(f"Successfully connected to Redis at {redis_url}")
        else:
            logger.error(f"Connected to Redis at {redis_url}, but ping failed")
            return False
        
        # List of key patterns to delete
        key_patterns = [
            'waf:*',          # WAF-related keys
            'axes:*',         # Django Axes (login attempt limiting)
            'ratelimit:*',    # Rate limiting
            'celery-task-*',  # Celery tasks
            'search:*',       # Search-related caches
            'query:*',        # Query caches
            'cache:*',        # General cache entries
        ]
        
        total_deleted = 0
        
        # Delete keys matching patterns
        for pattern in key_patterns:
            matching_keys = list(r.scan_iter(pattern))
            if matching_keys:
                num_keys = len(matching_keys)
                logger.info(f"Found {num_keys} keys matching '{pattern}'")
                
                # Delete in batches to prevent blocking Redis
                batch_size = 100
                for i in range(0, len(matching_keys), batch_size):
                    batch = matching_keys[i:i+batch_size]
                    if batch:
                        deleted = r.delete(*batch)
                        total_deleted += deleted
                        logger.info(f"Deleted {deleted} keys in batch")
            else:
                logger.info(f"No keys found matching '{pattern}'")
        
        # Option to completely flush all keys (be careful!)
        flush_all = len(sys.argv) > 1 and sys.argv[1] == "--flush-all"
        if flush_all:
            logger.warning("Flushing ALL Redis data!")
            r.flushall()
            logger.info("Redis database flushed completely")
        else:
            logger.info(f"Total keys deleted: {total_deleted}")
        
        return True
    
    except redis.RedisError as e:
        logger.error(f"Redis error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Redis clean-up...")
    
    if flush_redis():
        logger.info("Redis clean-up completed successfully")
        sys.exit(0)
    else:
        logger.error("Redis clean-up failed")
        sys.exit(1)