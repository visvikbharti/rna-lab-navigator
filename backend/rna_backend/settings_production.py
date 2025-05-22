"""
Production settings for Railway deployment
"""
import os
import dj_database_url
from .settings import *

# Override settings for production
DEBUG = False

# Railway automatically provides the RAILWAY_STATIC_URL
STATIC_URL = os.getenv('RAILWAY_STATIC_URL', '/static/')
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Railway domains and custom domains
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',  # Railway domain
    '.vercel.app',   # Frontend domain
]

# Add custom domains from environment
if os.getenv("ALLOWED_HOSTS"):
    ALLOWED_HOSTS += os.getenv("ALLOWED_HOSTS").split(",")

# Database configuration for Railway PostgreSQL
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
    }
else:
    # Fallback to individual PostgreSQL environment variables
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'railway'),
            'USER': os.getenv('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }

# Redis configuration for Railway
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Weaviate configuration for Railway
WEAVIATE_URL = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY', '')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in production")

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Content security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Referrer policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'https://rna-lab-navigator.vercel.app',  # Production frontend
]

# Add additional CORS origins from environment
if os.getenv("CORS_ALLOWED_ORIGINS"):
    CORS_ALLOWED_ORIGINS += os.getenv("CORS_ALLOWED_ORIGINS").split(",")

# Enhanced security headers for production
CSP_CONFIG = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:", "https:"],
    "script-src": ["'self'"],
    "style-src": ["'self'", "'unsafe-inline'"],  # Required for some CSS frameworks
    "connect-src": ["'self'", "https://api.openai.com"],
    "font-src": ["'self'"],
    "frame-src": ["'none'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
}

# Enable security features for production
WAF_ENABLED = True
WAF_SECURITY_LEVEL = 'medium'
ENABLE_RATE_LIMITING = True
SCAN_REQUESTS_FOR_PII = True

# Analytics and monitoring
ANALYTICS_ENABLED = True
ANALYTICS_MONITOR_SYSTEM = True

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'production.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.security': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'gunicorn.error': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'gunicorn.access': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Media files configuration for production
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Ensure required directories exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'figures'), exist_ok=True)