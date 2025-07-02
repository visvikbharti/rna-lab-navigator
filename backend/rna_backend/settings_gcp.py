"""
Google Cloud Platform production settings
"""
import os
import io
from google.cloud import secretmanager
from .settings import *

# GCP Project ID
GCP_PROJECT = os.getenv('GCP_PROJECT', 'your-gcp-project-id')

# Initialize Secret Manager client
secrets_client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_id, version_id="latest"):
    """Retrieve secret from Google Secret Manager"""
    try:
        name = f"projects/{GCP_PROJECT}/secrets/{secret_id}/versions/{version_id}"
        response = secrets_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        # Fallback to environment variable
        return os.getenv(secret_id.upper().replace('-', '_'))

# Core settings
DEBUG = False
SECRET_KEY = get_secret('django-secret-key') or os.getenv('SECRET_KEY')

# Allowed hosts - Cloud Run provides the service URL
ALLOWED_HOSTS = [
    '.run.app',  # Cloud Run domain
    'localhost',
    '127.0.0.1',
]

# Add custom domain if provided
if os.getenv("CUSTOM_DOMAIN"):
    ALLOWED_HOSTS.append(os.getenv("CUSTOM_DOMAIN"))

# Database - Cloud SQL
if os.getenv('DATABASE_URL'):
    # Use DATABASE_URL if provided (for local testing)
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
    }
else:
    # Cloud SQL connection
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'rna_lab_navigator'),
            'USER': os.getenv('DB_USER', 'rna_lab_user'),
            'PASSWORD': get_secret('db-password'),
            'HOST': f'/cloudsql/{GCP_PROJECT}:asia-south1:rna-lab-db',
            'PORT': '5432',
        }
    }

# Redis - Memorystore
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

# Celery configuration
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

# Static files - Cloud Storage
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME', f'{GCP_PROJECT}-static')
GS_PROJECT_ID = GCP_PROJECT
GS_DEFAULT_ACL = 'publicRead'
STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'

# Media files - Cloud Storage
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_MEDIA_BUCKET_NAME = os.getenv('GS_MEDIA_BUCKET_NAME', f'{GCP_PROJECT}-media')
MEDIA_URL = f'https://storage.googleapis.com/{GS_MEDIA_BUCKET_NAME}/'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'https://rna-lab-navigator.vercel.app',
]

# Add additional CORS origins from environment
if os.getenv("CORS_ALLOWED_ORIGINS"):
    CORS_ALLOWED_ORIGINS += os.getenv("CORS_ALLOWED_ORIGINS").split(",")

CORS_ALLOW_CREDENTIALS = True

# OpenAI configuration
OPENAI_API_KEY = get_secret('openai-api-key')

# Weaviate configuration
WEAVIATE_URL = os.getenv('WEAVIATE_URL', 'http://weaviate:8080')
WEAVIATE_API_KEY = get_secret('weaviate-api-key', required=False)

# Logging configuration for GCP
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Cloud Run specific settings
PORT = int(os.getenv('PORT', 8080))

# Trust proxy headers from Cloud Run
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Add GCP-specific middleware if needed
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Email backend for production (using SendGrid or Cloud Functions)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Change to proper backend

# Analytics and monitoring
ANALYTICS_ENABLED = True
ENABLE_CLOUD_LOGGING = True
ENABLE_CLOUD_TRACE = True
ENABLE_CLOUD_PROFILER = os.getenv('ENABLE_PROFILER', 'False') == 'True'