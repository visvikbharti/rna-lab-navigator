"""
PythonAnywhere-specific settings for RNA Lab Navigator
"""

import os
from .settings import *

# PythonAnywhere deployment flags
ENABLE_CROSS_ENCODER = False
ENABLE_LOCAL_EMBEDDINGS = False
ENABLE_OFFLINE_MODE = False
USE_SIMPLE_SEARCH = True

# Override debug setting
DEBUG = False

# PythonAnywhere specific allowed hosts
ALLOWED_HOSTS = ['rnalab.pythonanywhere.com', 'www.rnalab.pythonanywhere.com']

# Database configuration for PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rnalab$rna_lab_db',
        'USER': 'rnalab',
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),  # Set in PythonAnywhere env vars
        'HOST': 'rnalab.postgres.pythonanywhere-services.com',
        'PORT': os.environ.get('DB_PORT', ''),  # Set in PythonAnywhere env vars
    }
}

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = '/home/rnalab/rna-lab-navigator/backend/static'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/rnalab/rna-lab-navigator/backend/media'

# Security settings for production
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

# CORS settings - allow your Vercel frontend
CORS_ALLOWED_ORIGINS = [
    'https://rna-lab-navigator.vercel.app',
    'https://rna-lab-navigator-git-fix-openai-api-v1.vercel.app',
]

# Disable features that need more resources
CELERY_TASK_ALWAYS_EAGER = True  # No Celery workers on PythonAnywhere
USE_REDIS = False  # No Redis on free tier

# Weaviate configuration
# We'll use Weaviate Cloud or a simple PostgreSQL-based search
WEAVIATE_URL = os.environ.get('WEAVIATE_URL', '')
USE_SIMPLE_VECTOR_SEARCH = not bool(WEAVIATE_URL)

# Performance optimizations for PythonAnywhere
RAG_MAX_CONTEXT_CHUNKS = 2  # Reduce for faster responses
PRODUCTION_RAG_CACHE_TTL = 7200  # 2 hours cache
OPENAI_TIMEOUT = 60  # Increase timeout for PythonAnywhere

# Disable heavy middleware for PythonAnywhere
MIDDLEWARE = [
    # Security middleware
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # For static files
    # CORS
    "corsheaders.middleware.CorsMiddleware",
    # Standard Django middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Axes for security
    "axes.middleware.AxesMiddleware",
]

# Simplified logging for PythonAnywhere
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/home/rnalab/rna-lab-navigator/backend/error.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR',
    },
}

# WhiteNoise settings for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS settings for frontend
CORS_ALLOWED_ORIGINS = [
    'https://rna-lab-navigator.vercel.app',
    'https://rna-lab-navigator-git-fix-openai-api-v1.vercel.app',
    'https://rna-lab-navigator-git-pythonanywhere-deploy.vercel.app',
    'https://rna-lab-navigator-production.vercel.app',
    'https://rna-lab-navigator-production-ctbr1wtbw.vercel.app',  # Current deployment
    'http://localhost:5173',  # Local development
    'http://localhost:3000',  # Alternative local port
]

# Allow all Vercel preview deployments
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://rna-lab-navigator-.*\.vercel\.app$",
]

# Allow credentials for authentication
CORS_ALLOW_CREDENTIALS = True

# Allow these headers in CORS requests
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

print("PythonAnywhere settings loaded successfully!")