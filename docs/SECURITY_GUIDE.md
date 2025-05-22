# RNA Lab Navigator - Security Guide

This guide provides detailed information on the security measures implemented in the RNA Lab Navigator system. It's intended for developers working on the codebase and system administrators managing deployments.

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection](#data-protection)
4. [Secure Communication](#secure-communication)
5. [Protection Against Common Vulnerabilities](#protection-against-common-vulnerabilities)
6. [Operational Security](#operational-security)
7. [Security Verification](#security-verification)
8. [Customizing Security Settings](#customizing-security-settings)
9. [Troubleshooting](#troubleshooting)

## Security Architecture

The RNA Lab Navigator implements a defense-in-depth security approach:

```
                  ┌───────── Browser (Auth) ──────────┐
                  │  JWT           HTTPS              │
                  ▼                                   ▼
           Vercel Edge → Rate limiting → WAF (OWASP rules)
                  │
      ┌──────────TLS──────────┐
      ▼                       ▼
┌────────── Backend micro-Nets (Railway) ──────────┐
│  Gunicorn (Django)       Celery worker           │
│   │  AppSec headers (CSP,HSTS,XFO)               │
│   ▼                                              │
│  DRF auth → RBAC → input validation              │
│   │   (doc_type filter, query length)            │
│   ▼                                              │
│  Query service (vector) ─── mTLS ─▶ Weaviate (private IP) │
│                                         │
│  Postgres (RLS, AES-TDE) <─ audit logs  │
└──────────────────────────────────────────┘
                  │
                  ▼
           OpenAI API (TLS, key‐scoped, usage caps)
```

Key security components:

1. **Layered Security** - Multiple security controls at each layer protect against various attack vectors
2. **Security Headers** - Strong security headers protect against web vulnerabilities
3. **PII Detection** - Scanning and redaction of personal information
4. **Differential Privacy** - Protection for embeddings against inversion attacks
5. **Audit Logging** - Comprehensive logging for security events
6. **Connection Security** - Session management and connection timeout
7. **Automated Verification** - Regular checking of security settings

## Authentication & Authorization

### JWT Authentication

The system uses JWT tokens for authentication with the following settings:

- 24-hour access tokens
- 14-day refresh tokens
- HttpOnly, SameSite=Lax cookie storage
- PBKDF2 password hashing with high iteration count

### Role-Based Access Control (RBAC)

Three primary roles are implemented:

1. **Standard User**: Can query the system and view approved documents
2. **Staff User**: Can upload documents and manage document collections
3. **Admin User**: Full system access including security settings

Permissions are enforced both at the view level (DRF permissions) and at the model level (Django model permissions).

### Code Example

```python
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    
    def get_queryset(self):
        """Filter documents based on user permissions"""
        user = self.request.user
        
        # Admin sees all documents
        if user.is_staff:
            return Document.objects.all()
            
        # Regular users see only published documents
        return Document.objects.filter(status='published')
```

## Data Protection

### PII Detection and Redaction

The system includes an automated PII detection system to prevent sensitive information from being stored or returned in responses.

Key features:

- **Pattern Matching**: Regular expressions for common PII patterns
- **Named Entity Recognition**: ML-based detection of names, locations, etc.
- **Context-Aware Detection**: Distinguishes between PII and lab-specific identifiers
- **Automated Redaction**: Option to automatically redact detected PII

Configuration settings:

```python
# PII Detection and filtering settings
SCAN_REQUESTS_FOR_PII = True  # Scan incoming requests
SCAN_RESPONSES_FOR_PII = False  # Scan outgoing responses (high security mode)
AUTO_REDACT_PII = False  # Automatically redact detected PII
MAX_PII_SCAN_SIZE = 5 * 1024 * 1024  # 5MB maximum file size for PII scanning
```

### Differential Privacy for Embeddings

The system applies differential privacy to embeddings to prevent potential extraction of sensitive information from the vector database.

Key features:

- **Calibrated Noise**: Adds noise to embeddings with controlled privacy budget
- **Deterministic Noise**: Uses content hash to ensure consistent noise for the same content
- **Configurable Privacy Parameters**: Adjustable privacy-utility tradeoff

Configuration settings:

```python
# Differential privacy settings
ENABLE_DP_EMBEDDING_PROTECTION = True
DP_EPSILON = 0.1  # Privacy parameter (lower = more privacy)
DP_SENSITIVITY = 0.1  # L2 sensitivity of embeddings
DP_CLIP_NORM = 1.0  # Maximum L2 norm for clipping
DP_NOISE_MECHANISM = 'gaussian'  # 'gaussian' or 'laplace'
```

## Secure Communication

### TLS Configuration

All external communication uses TLS with secure settings:

- TLS 1.2+ only
- Strong cipher suites
- HSTS header with long duration
- Certificate validation

### Internal Communication

- Service-to-service communication uses mutual TLS (mTLS) where applicable
- Internal network segmentation isolates components
- Weaviate and database connections use private IPs

## Protection Against Common Vulnerabilities

### Content Security Policy (CSP)

The system implements a strong Content Security Policy to mitigate XSS and other client-side vulnerabilities.

Default CSP configuration:

```python
CSP_CONFIG = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:"],
    "script-src": ["'self'", "'unsafe-inline'"],  # For React
    "style-src": ["'self'", "'unsafe-inline'"],  # For React
    "connect-src": ["'self'", "localhost:*"],
    "font-src": ["'self'"],
    "frame-src": ["'none'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
}
```

### Other Security Headers

Additional security headers implemented:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

### SQL Injection Protection

- Django ORM used for database access with parameterized queries
- Explicit validation for any raw SQL
- Limited database privileges for application user

### CSRF Protection

- Django's built-in CSRF protection enabled
- CSRF tokens required for all non-GET requests
- SameSite cookie policy enforced

## Operational Security

### Connection Security

The system implements connection timeout and management to protect against session hijacking and resource exhaustion.

Configuration settings:

```python
# Connection security settings
ENABLE_CONNECTION_TIMEOUT = True
CONNECTION_TIMEOUT_SECONDS = 1800  # 30 minutes of inactivity
CONNECTION_CLEANUP_INTERVAL = 300  # 5 minutes between cleanup runs
MAX_CONNECTIONS_PER_IP = 10  # Maximum simultaneous connections per IP
```

### Secure Deployment

- Docker-based deployment with minimal images
- Regular security patching
- Secrets stored in environment variables or dedicated secrets store
- Health checks for all components

### Audit Logging

The system maintains detailed logs for security-relevant events:

- Authentication events (login, logout, failed attempts)
- Document access and modification
- Vector database operations
- Security setting changes
- PII detection events

## Security Verification

The system includes an automated security verification framework to ensure all security measures are correctly implemented.

### Running Security Verification

Via management command:

```bash
# Run all security checks
python manage.py verify_security

# Run specific check
python manage.py verify_security --check check_security_headers

# Generate detailed report
python manage.py verify_security --details --output report.json
```

Via admin interface:

1. Navigate to the admin site
2. Go to the "Security Dashboard"
3. Click "Run Security Verification"

### Checking Security Headers

```bash
python manage.py check_security --url https://your-domain.com
```

### Continuous Integration

The repository includes CI workflows for automated security checks:

- Static security analysis with bandit
- Dependency scanning with safety
- Secrets detection with detect-secrets
- Security configuration verification
- Headers compliance checking

## Customizing Security Settings

Security settings can be customized via:

1. **Environment variables**:
   ```bash
   # Example: Configure PII scanning
   export SCAN_REQUESTS_FOR_PII=True
   export AUTO_REDACT_PII=True
   ```

2. **Settings files**:
   - `settings.py` - Base settings
   - `settings_prod.py` - Production overrides
   - `settings_offline.py` - Offline mode settings

3. **Admin interface**:
   - Navigate to Security Dashboard
   - View and edit security settings

## Offline Mode

The system supports a fully offline mode for air-gapped environments:

- Local LLM using llama.cpp
- Local embedding models
- Local vector database (Qdrant, Chroma, or FAISS)
- File-based caching

To enable offline mode:

```bash
# Enable offline mode
export RNA_OFFLINE=true

# Start the server with offline settings
python manage.py runserver --settings=rna_backend.settings_offline
```

## Troubleshooting

### Common Issues

#### Security Settings Not Applied

**Symptom**: Security headers or other settings not being applied

**Solution**:
1. Check if middleware is correctly ordered
2. Verify settings are loaded (try `print(settings.DEBUG)` in a view)
3. Check for overrides in environment variables

#### PII Detection Issues

**Symptom**: False positives or false negatives in PII detection

**Solution**:
1. Review detected patterns in logs
2. Add lab-specific safe patterns to `LAB_SAFE_PATTERNS`
3. Adjust strictness with `strict_mode=False` parameter

#### Performance Issues with Security Features

**Symptom**: Slow performance with security features enabled

**Solution**:
1. Disable `SCAN_RESPONSES_FOR_PII` unless needed
2. Increase `MAX_PII_SCAN_SIZE`
3. Adjust `CONNECTION_CLEANUP_INTERVAL`

---

## Security Contact

For security issues, please contact:

- Security Team: security@RNA-lab-navigator.org
- Principal Investigator: Dr. Debojyoti Chakraborty

---

This documentation should be reviewed and updated with each major release.