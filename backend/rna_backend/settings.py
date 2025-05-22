import os
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Custom JSON encoder to handle PosixPath objects
class PathJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

# Apply custom JSON encoder globally
json.JSONEncoder = PathJSONEncoder

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Media files directory for storing extracted figures
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Create media directory if it doesn't exist
os.makedirs(os.path.join(MEDIA_ROOT, 'figures'), exist_ok=True)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-x9w2m5p7q8r3t6y9u1i4o7p0a3s6d9f2g5h8j1k4l7m0n3q6r9t2u5v8w1x4y7z0a3b6c9d2e5f8g1h4j7k0l3m6n9o2p5q8r4t7u0v3w6x9y2z5a8b1c4d7e0f3g6h9i2j5k8l1m4n7o0p3q6r9s2t5u8v1w4x7y0z3a6b9c2d5e8f1g4h7i0j3k6l9m2n5o8p1q4r7s0t3u6v9w2x5y8z1")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
if os.getenv("ALLOWED_HOSTS"):
    ALLOWED_HOSTS += os.getenv("ALLOWED_HOSTS").split(",")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "axes",
    # Local apps
    "api",
    "api.analytics.apps.AnalyticsConfig",  # Analytics subapp
    "api.auth.apps.AuthConfig",  # Auth subapp
    "api.security.apps.SecurityConfig",  # Security subapp
    "api.quality.apps.QualityConfig",  # Quality subapp
    "api.feedback.apps.FeedbackConfig",  # Feedback subapp
    "api.search.apps.SearchConfig",  # Search subapp
]

# Authentication backends
AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend should be the first backend in the AUTHENTICATION_BACKENDS list
    'axes.backends.AxesStandaloneBackend',
    # Django's default ModelBackend for model-based authentication
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    # Security middleware should be first
    "api.security.error_handling.SecurityMiddleware",  # Security error handling (must be first)
    "django.middleware.security.SecurityMiddleware",
    # CORS should be early to handle preflight requests
    "corsheaders.middleware.CorsMiddleware",
    # Standard Django middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Axes middleware should be after auth middleware
    "axes.middleware.AxesMiddleware",  # Login attempt tracking and brute force protection
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom security middleware
    "api.security.headers.SecurityHeadersMiddleware",  # Security headers
    "api.security.waf.WAFMiddleware",  # Web Application Firewall protection
    "api.security.rate_limiting.RateLimitingMiddleware",  # API rate limiting
    "api.security.middleware.PIIFilterMiddleware",  # PII detection and filtering
    "api.security.connection.ConnectionTimeoutMiddleware",  # Connection timeout enforcement
    # Analytics should be last to capture all data
    "api.analytics.middleware.AnalyticsMiddleware",  # Analytics data collection
]

# Configure django-axes behind reverse proxy (using new settings)
# Removed deprecated AXES_PROXY_COUNT in favor of AXES_IPWARE_PROXY_COUNT
AXES_IPWARE_PROXY_COUNT = 1  # Number of proxies in front of the application
AXES_IPWARE_META_PRECEDENCE_ORDER = [
    "HTTP_X_FORWARDED_FOR",
    "REMOTE_ADDR",
]

# PII Detection and filtering settings
SCAN_REQUESTS_FOR_PII = True
SCAN_RESPONSES_FOR_PII = False  # Enable only in high-security environments
AUTO_REDACT_PII = False  # Set to True to automatically redact detected PII
MAX_PII_SCAN_SIZE = 5 * 1024 * 1024  # 5MB maximum file size for PII scanning

# Rate limiting settings
ENABLE_RATE_LIMITING = True
RATE_LIMIT_DEFAULT = "60/minute"  # Default rate limit for all API endpoints
RATE_LIMIT_EXEMPTIONS = []  # List of exempted IPs or user IDs
RATE_LIMIT_RULES = {
    "/api/query/": "30/minute",  # Main search query endpoint
    "/api/search/": "40/minute",  # General search endpoint
    "/api/auth/login/": "10/minute",  # Login attempts
    "/api/auth/register/": "5/hour",  # Registration attempts
    "/api/upload/": "10/hour",  # Document uploads
}
RATE_LIMIT_BLOCK_DURATION = 300  # 5 minutes block for limit violations
RATE_LIMIT_ANALYTICS = True  # Log rate limit events

# Web Application Firewall (WAF) settings
WAF_ENABLED = False  # Enable WAF protection
WAF_EXCLUDED_PATHS = [
    '/admin/',      # Admin panel has its own security
    '/static/',     # Static files don't need WAF protection
    '/media/',      # Media files don't need WAF protection
    '/health/',     # Health check endpoint (doesn't contain user input)
]
WAF_SECURITY_LEVEL = 'low'  # Options: 'low', 'medium', 'high'
WAF_BLOCK_IP_DURATION = 600  # 10 minutes block for repeated attacks
WAF_MAX_VIOLATIONS = 3  # Number of violations before blocking IP

# Connection security settings
ENABLE_CONNECTION_TIMEOUT = True
CONNECTION_TIMEOUT_SECONDS = 1800  # 30 minutes of inactivity
CONNECTION_CLEANUP_INTERVAL = 300  # 5 minutes between cleanup runs
MAX_CONNECTIONS_PER_IP = 10  # Maximum simultaneous connections per IP

# Differential privacy settings
ENABLE_DP_EMBEDDING_PROTECTION = True  # Enable differential privacy for embeddings
DP_EPSILON = 0.1  # Privacy parameter (lower = more privacy)
DP_SENSITIVITY = 0.1  # L2 sensitivity of embeddings
DP_CLIP_NORM = 1.0  # Maximum L2 norm for clipping
DP_NOISE_MECHANISM = 'gaussian'  # 'gaussian' or 'laplace'

# Security headers settings
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')
SECURITY_HEADERS_MONITORING = True
CSP_CONFIG = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:"],
    "script-src": ["'self'", "'unsafe-inline'"],  # Unsafe-inline needed for React
    "style-src": ["'self'", "'unsafe-inline'"],  # Unsafe-inline needed for React
    "connect-src": ["'self'", "localhost:*"],
    "font-src": ["'self'"],
    "frame-src": ["'none'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
}

ROOT_URLCONF = "rna_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "rna_backend.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Use SQLite for demo purposes
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Commented out PostgreSQL configuration
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.getenv("POSTGRES_DB", "rna_db"),
#         "USER": os.getenv("POSTGRES_USER", "postgres"),
#         "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
#         "HOST": os.getenv("POSTGRES_HOST", "localhost"),
#         "PORT": os.getenv("POSTGRES_PORT", "5432"),
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Celery settings
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"  # Golden rule #4

# Backup settings
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
BACKUP_CLEANUP_LOCAL = os.getenv("BACKUP_CLEANUP_LOCAL", "False") == "True"
AWS_BACKUP_BUCKET = os.getenv("AWS_BACKUP_BUCKET", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT", "")

# Cache settings (used for rate limiting)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Weaviate settings
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")

# Weaviate mTLS settings
WEAVIATE_TLS_ENABLED = os.getenv("WEAVIATE_TLS_ENABLED", "False") == "True"
WEAVIATE_CLIENT_CERT = os.getenv("WEAVIATE_CLIENT_CERT", "")
WEAVIATE_CLIENT_KEY = os.getenv("WEAVIATE_CLIENT_KEY", "")
WEAVIATE_CA_CERT = os.getenv("WEAVIATE_CA_CERT", "")

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))

# LLM network isolation settings
LLM_NETWORK_ISOLATION = os.getenv("LLM_NETWORK_ISOLATION", "False") == "True"
LLM_FORCE_ISOLATION = os.getenv("LLM_FORCE_ISOLATION", "False") == "True"
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# Local embedding model settings
LOCAL_EMBEDDING_MODEL_PATH = os.getenv("LOCAL_EMBEDDING_MODEL_PATH", "")
LOCAL_EMBEDDING_TOKENIZER_PATH = os.getenv("LOCAL_EMBEDDING_TOKENIZER_PATH", "")
LOCAL_EMBEDDING_DIMENSION = int(os.getenv("LOCAL_EMBEDDING_DIMENSION", "768"))

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security settings for production
if not DEBUG:
    # HTTPS settings
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
else:
    # Development settings - less restrictive for local development
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'  # More secure for development too

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only allow all origins in development
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # Vite dev server
    'http://127.0.0.1:5173',  # Alternative local dev
    'https://rna-lab-navigator.vercel.app',  # Production frontend
]
if os.getenv("CORS_ALLOWED_ORIGINS"):
    CORS_ALLOWED_ORIGINS += os.getenv("CORS_ALLOWED_ORIGINS").split(",")

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = [
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

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # Changed for demo purposes
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "60/minute",
    },
    "EXCEPTION_HANDLER": "api.security.error_handling.custom_exception_handler",
}

# Chunking settings (Golden rule #1)
CHUNK_SIZE = 400
CHUNK_OVERLAP = 100

# Analytics settings
ANALYTICS_ENABLED = True
ANALYTICS_RETENTION_DAYS = 90  # Days to keep raw analytics data
ANALYTICS_MONITOR_SYSTEM = True  # Enable system performance monitoring
ANALYTICS_SENSITIVE_PATHS = [
    '/admin/',
    '/api/auth/',
    '/api/users/',
]  # Paths containing sensitive operations to audit

# JWT Authentication settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=15),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    
    # Security enhancements
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
    'SLIDING_TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer',
    'SLIDING_TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer',
}

# Django-Axes for login security (updated settings)
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5  # Number of failed login attempts before lockout
AXES_LOCK_OUT_AT_FAILURE = True  # Lock out user after failed login attempts
AXES_COOLOFF_TIME = 1  # Lock out for 1 hour (in hours)
AXES_LOCKOUT_TEMPLATE = None  # No custom template, return 403 response
AXES_LOCKOUT_URL = None  # No custom lockout URL
AXES_RESET_ON_SUCCESS = True  # Reset failed login attempts after successful login
AXES_ENABLE_USER_AGENT = True  # New setting to replace AXES_USE_USER_AGENT
AXES_CACHE = 'default'  # Use the default cache for tracking login attempts
AXES_HANDLER = 'axes.handlers.cache.AxesCacheHandler'  # Use cache handler for storage

# Logging configuration for security monitoring
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'api.security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'axes': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)