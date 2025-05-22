# Configuration Reference

This document provides a comprehensive reference for all configuration options in the RNA Lab Navigator system.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Django Settings](#django-settings)
3. [Docker Compose Configuration](#docker-compose-configuration)
4. [Weaviate Configuration](#weaviate-configuration)
5. [OpenAI Configuration](#openai-configuration)
6. [Network Isolation Configuration](#network-isolation-configuration)
7. [Security Configuration](#security-configuration)
8. [Backup Configuration](#backup-configuration)
9. [Performance Tuning](#performance-tuning)
10. [Logging Configuration](#logging-configuration)

## Environment Variables

### Core Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG` | Enable debug mode | `False` | No |
| `SECRET_KEY` | Django secret key | - | Yes |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` | Yes |
| `TIME_ZONE` | Timezone for the application | `Asia/Kolkata` | Yes |

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_HOST` | PostgreSQL host | `postgres` | Yes |
| `DB_PORT` | PostgreSQL port | `5432` | Yes |
| `DB_NAME` | PostgreSQL database name | `rna_db` | Yes |
| `DB_USER` | PostgreSQL username | `rna_user` | Yes |
| `DB_PASSWORD` | PostgreSQL password | - | Yes |

### Redis Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_HOST` | Redis host | `redis` | Yes |
| `REDIS_PORT` | Redis port | `6379` | Yes |
| `REDIS_PASSWORD` | Redis password | - | Yes |
| `REDIS_DB` | Redis database index | `0` | No |
| `REDIS_CACHE_DB` | Redis database for caching | `1` | No |

### Celery Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CELERY_BROKER_URL` | Celery broker URL | `redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0` | No |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0` | No |
| `CELERY_TASK_ALWAYS_EAGER` | Run tasks synchronously | `False` | No |
| `CELERY_TIMEZONE` | Timezone for Celery | Same as `TIME_ZONE` | No |
| `CELERY_WORKER_CONCURRENCY` | Number of worker processes | `Auto (CPU count)` | No |

### Storage Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MEDIA_ROOT` | Path to media files | `/app/media` | No |
| `STATIC_ROOT` | Path to static files | `/app/staticfiles` | No |
| `USE_S3_STORAGE` | Use S3 for media storage | `False` | No |
| `S3_BUCKET_NAME` | S3 bucket name | - | If `USE_S3_STORAGE=True` |
| `S3_ACCESS_KEY` | S3 access key | - | If `USE_S3_STORAGE=True` |
| `S3_SECRET_KEY` | S3 secret key | - | If `USE_S3_STORAGE=True` |
| `S3_ENDPOINT_URL` | S3 endpoint URL | `https://s3.amazonaws.com` | No |
| `S3_REGION_NAME` | S3 region name | `us-east-1` | No |

## Django Settings

Key Django settings that can be configured:

### Site Configuration

```python
# Configured via environment variables
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
TIME_ZONE = os.environ.get('TIME_ZONE', 'Asia/Kolkata')
```

### Database Configuration

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'rna_db'),
        'USER': os.environ.get('DB_USER', 'rna_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### Cache Configuration

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://:{ os.environ.get('REDIS_PASSWORD', '') }@{ os.environ.get('REDIS_HOST', 'redis') }:{ os.environ.get('REDIS_PORT', '6379') }/{ os.environ.get('REDIS_CACHE_DB', '1') }",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# Query cache settings
QUERY_CACHE_ENABLED = os.environ.get('QUERY_CACHE_ENABLED', 'True') == 'True'
QUERY_CACHE_TTL = int(os.environ.get('QUERY_CACHE_TTL', '86400'))  # 24 hours by default
```

### Security Settings

```python
# Security settings
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True'
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### REST Framework Settings

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '60/minute',
        'query': '100/day',
        'feedback': '100/day',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

## Docker Compose Configuration

### Development Configuration

The default `docker-compose.yml` for development:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  weaviate:
    image: semitechnologies/weaviate:1.17.2
    ports:
      - "8080:8080"
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=text2vec-openai
      - ENABLE_MODULES=text2vec-openai,generative-openai
      - CLUSTER_HOSTNAME=node1
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  weaviate_data:
```

### Production Configuration

The production `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
      - weaviate
    env_file:
      - ./backend/.env
    volumes:
      - ./media:/app/media
      - ./static:/app/staticfiles
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A rna_backend worker -l info
    restart: unless-stopped
    depends_on:
      - backend
      - redis
    env_file:
      - ./backend/.env
    volumes:
      - ./media:/app/media

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A rna_backend beat -l info
    restart: unless-stopped
    depends_on:
      - backend
      - redis
    env_file:
      - ./backend/.env

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  weaviate:
    image: semitechnologies/weaviate:1.17.2
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=text2vec-openai
      - ENABLE_MODULES=text2vec-openai,generative-openai
      - CLUSTER_HOSTNAME=node1
    volumes:
      - weaviate_data:/var/lib/weaviate
      - ./certs/weaviate:/certs
    restart: unless-stopped

  nginx:
    image: nginx:1.21
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./static:/var/www/static
      - ./media:/var/www/media
      - ./frontend/dist:/var/www/html
      - ./certs/nginx:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  weaviate_data:
```

### Air-Gapped Configuration

The air-gapped `docker-compose.air-gapped.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
      - weaviate
      - ollama
    env_file:
      - ./backend/.env
    volumes:
      - ./media:/app/media
      - ./static:/app/staticfiles
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A rna_backend worker -l info
    restart: unless-stopped
    depends_on:
      - backend
      - redis
    env_file:
      - ./backend/.env
    volumes:
      - ./media:/app/media

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A rna_backend beat -l info
    restart: unless-stopped
    depends_on:
      - backend
      - redis
    env_file:
      - ./backend/.env

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  weaviate:
    image: semitechnologies/weaviate:1.17.2
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=none
      - CLUSTER_HOSTNAME=node1
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ./models:/root/.ollama
    restart: unless-stopped

  nginx:
    image: nginx:1.21
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./static:/var/www/static
      - ./media:/var/www/media
      - ./frontend/dist:/var/www/html
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  weaviate_data:
```

## Weaviate Configuration

### Connection Configuration

```python
# In settings.py
WEAVIATE_URL = os.environ.get('WEAVIATE_URL', 'http://weaviate:8080')
WEAVIATE_MTLS_ENABLED = os.environ.get('WEAVIATE_MTLS_ENABLED', 'False') == 'True'
WEAVIATE_CERT_PATH = os.environ.get('WEAVIATE_CERT_PATH', '/app/certs/client.pem')
WEAVIATE_KEY_PATH = os.environ.get('WEAVIATE_KEY_PATH', '/app/certs/client.key')
WEAVIATE_CA_PATH = os.environ.get('WEAVIATE_CA_PATH', '/app/certs/ca.pem')
```

### Collection Schema

Key Weaviate collections used by the system:

```python
# Document schema
document_class = {
    "class": "Document",
    "description": "A document chunk from lab documents",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "text-embedding-ada-002",
            "modelVersion": "002",
            "type": "text"
        }
    },
    "properties": [
        {
            "name": "content",
            "description": "The text content of the document chunk",
            "dataType": ["text"]
        },
        {
            "name": "title",
            "description": "The title of the document",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": False,
                    "vectorizePropertyName": False
                }
            },
            "indexInverted": True
        },
        {
            "name": "doc_type",
            "description": "The type of document (protocol, paper, thesis, etc.)",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        },
        {
            "name": "author",
            "description": "Author of the document",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        },
        {
            "name": "year",
            "description": "Publication year",
            "dataType": ["int"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        },
        {
            "name": "chapter",
            "description": "Chapter or section of the document",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        },
        {
            "name": "chunk_id",
            "description": "Unique identifier for the chunk within the document",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        }
    ]
}

# Figure schema
figure_class = {
    "class": "Figure",
    "description": "A figure extracted from a document",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "text-embedding-ada-002",
            "modelVersion": "002",
            "type": "text"
        }
    },
    "properties": [
        {
            "name": "caption",
            "description": "The caption of the figure",
            "dataType": ["text"]
        },
        {
            "name": "figure_id",
            "description": "Unique identifier for the figure",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        },
        {
            "name": "figure_type",
            "description": "Type of figure (image, graph, table, etc.)",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        },
        {
            "name": "title",
            "description": "The title of the document containing the figure",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": False,
                    "vectorizePropertyName": False
                }
            },
            "indexInverted": True
        },
        {
            "name": "doc_type",
            "description": "The type of document containing the figure",
            "dataType": ["string"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        },
        {
            "name": "page_number",
            "description": "Page number where the figure appears",
            "dataType": ["int"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True
                }
            },
            "indexInverted": True
        }
    ]
}
```

### Search Configuration

```python
# Default search parameters
WEAVIATE_SEARCH_LIMIT = 10
WEAVIATE_HYBRID_ALPHA = 0.75  # Balance between vector and keyword search
WEAVIATE_DEFAULT_COLLECTION = "Document"
WEAVIATE_USE_HYBRID = True
```

## OpenAI Configuration

```python
# OpenAI API settings
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_ORG_ID = os.environ.get('OPENAI_ORG_ID', '')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
OPENAI_EMBEDDING_MODEL = os.environ.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')

# Model tier configuration
MODEL_TIERS = {
    'small': os.environ.get('SMALL_MODEL', 'gpt-3.5-turbo'),
    'default': os.environ.get('DEFAULT_MODEL', OPENAI_MODEL),
    'large': os.environ.get('LARGE_MODEL', 'gpt-4o'),
}

# Embedding dimensions
EMBEDDING_DIMENSIONS = 1536  # For Ada-002
```

## Network Isolation Configuration

```python
# Network isolation settings
LLM_ISOLATION_LEVEL = os.environ.get('LLM_ISOLATION_LEVEL', 'none')  # none, proxy, air-gapped
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://ollama:11434')

# Proxy settings (if using proxy isolation)
HTTP_PROXY = os.environ.get('HTTP_PROXY', '')
HTTPS_PROXY = os.environ.get('HTTPS_PROXY', '')
NO_PROXY = os.environ.get('NO_PROXY', 'localhost,127.0.0.1,redis,postgres,weaviate')

# Local model mappings for air-gapped mode
LOCAL_MODEL_MAPPINGS = {
    'gpt-3.5-turbo': os.environ.get('LOCAL_SMALL_MODEL', 'llama2:7b'),
    'gpt-4o': os.environ.get('LOCAL_DEFAULT_MODEL', 'mistral:7b'),
    'gpt-4-turbo': os.environ.get('LOCAL_LARGE_MODEL', 'orca2:7b'),
}

# Local embedding model for air-gapped mode
LOCAL_EMBEDDING_MODEL = os.environ.get('LOCAL_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
```

## Security Configuration

### Authentication Settings

```python
# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # Add LDAP or other authentication backends as needed
]
```

### Security Headers

```python
# Security middleware
MIDDLEWARE = [
    # ... other middleware
    'django.middleware.security.SecurityMiddleware',
    'api.security.middleware.SecurityHeadersMiddleware',
    'api.security.middleware.RateLimitingMiddleware',
    'api.security.middleware.IPBlockingMiddleware',
    # ... other middleware
]

# Content Security Policy settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'", "https://api.openai.com")
CSP_FONT_SRC = ("'self'",)
```

### Rate Limiting

```python
# Rate limiting settings
RATE_LIMITING_ENABLED = os.environ.get('RATE_LIMITING_ENABLED', 'True') == 'True'
RATE_LIMIT_ANONYMOUS = os.environ.get('RATE_LIMIT_ANONYMOUS', '30/minute')
RATE_LIMIT_USER = os.environ.get('RATE_LIMIT_USER', '60/minute')
RATE_LIMIT_QUERY = os.environ.get('RATE_LIMIT_QUERY', '100/day')
```

### IP Blocking

```python
# IP blocking settings
IP_BLOCKING_ENABLED = os.environ.get('IP_BLOCKING_ENABLED', 'True') == 'True'
IP_WHITELIST = os.environ.get('IP_WHITELIST', '').split(',')
IP_BLACKLIST = os.environ.get('IP_BLACKLIST', '').split(',')
AUTO_BLOCK_THRESHOLD = int(os.environ.get('AUTO_BLOCK_THRESHOLD', '10'))  # Auto-block after 10 security events
```

### mTLS Configuration

```python
# Generate self-signed certificates for development
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.pem -subj "/CN=RNA Lab Navigator CA"

# Generate server certificate
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=weaviate"
openssl x509 -req -days 365 -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out server.pem

# Generate client certificate
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=backend"
openssl x509 -req -days 365 -in client.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out client.pem
```

## Backup Configuration

```python
# Backup settings
BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'True') == 'True'
BACKUP_STORAGE = os.environ.get('BACKUP_STORAGE', 'local')  # local or s3
BACKUP_PATH = os.environ.get('BACKUP_PATH', '/app/backups')
BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))

# Schedule settings (in crontab format)
BACKUP_SCHEDULE = {
    'database': os.environ.get('DB_BACKUP_SCHEDULE', '0 2 * * *'),  # Daily at 2 AM
    'weaviate': os.environ.get('WEAVIATE_BACKUP_SCHEDULE', '0 3 * * 0'),  # Weekly on Sunday at 3 AM
    'media': os.environ.get('MEDIA_BACKUP_SCHEDULE', '0 4 1 * *'),  # Monthly on the 1st at 4 AM
}

# S3 backup settings
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', '')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', '')
S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL', 'https://s3.amazonaws.com')
S3_REGION_NAME = os.environ.get('S3_REGION_NAME', 'us-east-1')
```

## Performance Tuning

### Chunking Configuration

```python
# Chunking settings
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '400'))  # Words per chunk
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', '100'))  # Overlap between chunks
MAX_CHUNKS_PER_DOC = int(os.environ.get('MAX_CHUNKS_PER_DOC', '1000'))
```

### Query Processing

```python
# Query processing settings
MAX_RESULTS_PER_QUERY = int(os.environ.get('MAX_RESULTS_PER_QUERY', '10'))
CONTEXT_LIMIT = int(os.environ.get('CONTEXT_LIMIT', '3'))  # Number of documents in context
MIN_CONFIDENCE_THRESHOLD = float(os.environ.get('MIN_CONFIDENCE_THRESHOLD', '0.45'))
CACHE_CONFIDENCE_THRESHOLD = float(os.environ.get('CACHE_CONFIDENCE_THRESHOLD', '0.6'))
```

### Database Performance

```python
# Database performance settings
DB_CONN_MAX_AGE = int(os.environ.get('DB_CONN_MAX_AGE', '60'))  # Seconds
DB_TIMEOUT = int(os.environ.get('DB_TIMEOUT', '5'))  # Seconds
DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '20'))
```

### Weaviate Performance

```python
# Weaviate performance tuning
WEAVIATE_VECTOR_INDEX_TYPE = 'hnsw'  # Hierarchical Navigable Small World
WEAVIATE_VECTOR_INDEX_CONFIG = {
    'efConstruction': 128,  # Higher values = more accurate but slower indexing
    'maxConnections': 64    # Higher values = more accurate but higher memory usage
}
WEAVIATE_DISTANCE_METRIC = 'cosine'  # Cosine similarity for OpenAI embeddings
```

## Logging Configuration

```python
# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('LOG_FILE', '/app/logs/app.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'json_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('JSON_LOG_FILE', '/app/logs/app.json'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'api': {
            'handlers': ['console', 'file', 'json_file'],
            'level': os.environ.get('API_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'security': {
            'handlers': ['console', 'json_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Debug logging (only in development)
if DEBUG:
    LOGGING['loggers']['django']['level'] = 'DEBUG'
    LOGGING['loggers']['api']['level'] = 'DEBUG'
```