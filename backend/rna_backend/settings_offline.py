"""
Settings for offline/air-gapped mode.
This configuration replaces external dependencies with local alternatives.
"""

from .settings import *  # Import the base settings

# Mark the system as running in offline mode
OFFLINE_MODE = True

# Replace OpenAI with local Llama.cpp or another local model
OPENAI_API_KEY = None  # Disable OpenAI
USE_LOCAL_LLM = True
LOCAL_LLM_CONFIG = {
    "model_path": os.path.join(BASE_DIR, "models", "llm"),
    "model_name": "llama2-7b-chat.gguf",  # Default for Llama.cpp
    "ctx_size": 4096,
    "n_gpu_layers": -1,  # Use all available GPU layers
    "embedding_model_path": os.path.join(BASE_DIR, "models", "embeddings", "all-MiniLM-L6-v2"),
}

# Configure Cross Encoder to use local model
CROSS_ENCODER_CONFIG = {
    "model_path": os.path.join(BASE_DIR, "models", "cross-encoder", "ms-marco-MiniLM-L-6-v2"),
    "use_local": True
}

# Use SQLite for offline development and testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Use file-based cache instead of Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(BASE_DIR, "cache"),
    }
}

# Celery configuration for offline mode (using filesystem broker)
CELERY_BROKER_URL = f"filesystem://{os.path.join(BASE_DIR, 'celery_broker')}"
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "data_folder_in": os.path.join(BASE_DIR, "celery_broker", "in"),
    "data_folder_out": os.path.join(BASE_DIR, "celery_broker", "out"),
    "data_folder_processed": os.path.join(BASE_DIR, "celery_broker", "processed"),
}
CELERY_RESULT_BACKEND = "file://" + os.path.join(BASE_DIR, "celery_results")

# Ensure dirs exist for Celery filesystem broker
for dir_path in [CELERY_BROKER_TRANSPORT_OPTIONS["data_folder_in"],
                CELERY_BROKER_TRANSPORT_OPTIONS["data_folder_out"],
                CELERY_BROKER_TRANSPORT_OPTIONS["data_folder_processed"]]:
    os.makedirs(dir_path, exist_ok=True)

# Vector storage using SQLite-based Qdrant instead of Weaviate
WEAVIATE_URL = None  # Disable Weaviate
WEAVIATE_API_KEY = None
USE_LOCAL_VECTOR_DB = True
LOCAL_VECTOR_DB_CONFIG = {
    "engine": "qdrant",  # or "chroma", "faiss"
    "path": os.path.join(BASE_DIR, "vector_db"),
}

# Disable network-dependent components
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

# Enhanced security for offline mode
DEBUG = False
SECURE_SSL_REDIRECT = False  # Don't redirect in offline mode
SESSION_COOKIE_SECURE = False  # Allow non-HTTPS cookies in offline mode
CSRF_COOKIE_SECURE = False  # Allow non-HTTPS CSRF in offline mode

# Enable Content Security Policy with no external resources
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware"] + MIDDLEWARE
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_FONT_SRC = ("'self'",)

# Logging setup for offline mode (file-based)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "rna_backend.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "api": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Create logs directory
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)