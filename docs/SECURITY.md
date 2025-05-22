# RNA Lab Navigator - Security Overview

## Quick Reference

| Security Feature | Status | Configuration |
|------------------|--------|---------------|
| HTTPS/TLS | ✅ Enabled | Enforced with HSTS |
| Authentication | ✅ JWT | 24h access / 14d refresh |
| Authorization | ✅ RBAC | User/Staff/Admin roles |
| PII Detection | ✅ Enabled | `SCAN_REQUESTS_FOR_PII=True` |
| Differential Privacy | ✅ Enabled | `DP_EPSILON=0.1` |
| Security Headers | ✅ Enabled | CSP, X-Frame-Options, etc. |
| Connection Security | ✅ Enabled | 30-minute timeout |
| Offline Mode | ✅ Available | `RNA_OFFLINE=true` |
| Automated Checks | ✅ Enabled | CI pipeline + verification |

## Security Command Reference

```bash
# Verify security configuration
python manage.py verify_security

# Check security headers
python manage.py check_security

# Run security CI checks locally
./.github/workflows/scripts/run_security_checks.sh

# Enable offline mode
export RNA_OFFLINE=true
python manage.py runserver --settings=rna_backend.settings_offline
```

## Key Security Files

- `/backend/api/security/` - Security module
  - `pii_detector.py` - PII detection and redaction
  - `differential_privacy.py` - Embedding protection
  - `connection.py` - Session management
  - `headers.py` - Security headers
  - `verification.py` - Security verification

- `/docs/SECURITY_GUIDE.md` - Comprehensive security documentation

## Default Security Settings

```python
# PII Detection
SCAN_REQUESTS_FOR_PII = True
AUTO_REDACT_PII = False

# Differential Privacy
ENABLE_DP_EMBEDDING_PROTECTION = True
DP_EPSILON = 0.1

# Connection Security
ENABLE_CONNECTION_TIMEOUT = True
CONNECTION_TIMEOUT_SECONDS = 1800
```

For detailed information, see [SECURITY_GUIDE.md](SECURITY_GUIDE.md).