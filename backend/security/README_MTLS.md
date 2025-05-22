# Mutual TLS (mTLS) Setup for Weaviate

This directory contains tools for implementing mutual TLS (mTLS) authentication between the Django backend and Weaviate vector database, as specified in Sprint 3 of the security plan.

## 1. Overview

Mutual TLS (mTLS) provides two-way authentication, ensuring both the client and server verify each other's identity. This implementation:

1. Secures communication between Django backend and Weaviate
2. Ensures only authorized clients can access the vector database
3. Prevents unauthorized access even if the network is compromised

## 2. Certificate Generation

To generate certificates for development/testing:

```bash
# Install required package
pip install cryptography

# Create certificates in ./certs directory
python generate_mtls_certs.py --output-dir ./certs

# Load the environment variables (for Linux/Mac)
source ./certs/mtls.env

# Or on Windows
# set /p vars=<./certs/mtls.env
```

The script generates:
- A Certificate Authority (CA) certificate
- Server certificate for Weaviate
- Client certificate for Django
- Environment variables file (mtls.env)

## 3. Configure Weaviate

Edit `docker-compose.yml` to enable mTLS:

1. Uncomment the mTLS configuration lines:
   ```yaml
   environment:
     # ...other environment variables...
     - ENABLE_MTLS=true
     - MTLS_CA_FILE=/certs/ca-cert.pem
     - MTLS_SERVER_CERT_FILE=/certs/server-cert.pem
     - MTLS_SERVER_KEY_FILE=/certs/server-key.pem
   volumes:
     - weaviate_data:/var/lib/weaviate
     - ./backend/security/certs:/certs
   ```

2. Set the environment variable before starting Docker Compose:
   ```bash
   export MTLS_CERTS_DIR="$(pwd)/backend/security/certs"
   export ENABLE_MTLS=true
   
   # Then start containers
   docker-compose up -d
   ```

## 4. Configure Django

1. Add these environment variables to your `.env` file:
   ```
   WEAVIATE_TLS_ENABLED=True
   WEAVIATE_CLIENT_CERT=/path/to/client-cert.pem
   WEAVIATE_CLIENT_KEY=/path/to/client-key.pem
   WEAVIATE_CA_CERT=/path/to/ca-cert.pem
   ```

2. For development, you can source the generated configuration:
   ```bash
   source ./backend/security/certs/mtls.env
   
   # Start Django server
   cd backend && python manage.py runserver
   ```

## 5. Test the Connection

Test the mTLS connection between Django and Weaviate:

```bash
# Make sure environment variables are set
source ./backend/security/certs/mtls.env

# Run the test script
python test_mtls_connection.py
```

If successful, you should see:
```
✅ Successfully connected to Weaviate version X.Y.Z using mTLS
```

## 6. Production Deployment

For production deployment:

1. **Use a proper certificate management system** instead of self-signed certificates
2. Configure Railway to inject certificate data as environment variables
3. Store certificates securely, never in Git
4. Implement regular certificate rotation (e.g., quarterly)
5. Set up monitoring for certificate expiration

## 7. Troubleshooting

Common issues:

1. **Connection refused**: Ensure Weaviate is running and correctly configured with mTLS
2. **Certificate validation failed**: Verify the certificate paths and that the CA is correct
3. **Certificate not found**: Check file paths and permissions
4. **Handshake failed**: Ensure certificates are compatible with TLS 1.2+

For detailed debugging:

```bash
# Enable verbose logging
export WEAVIATE_LOG_LEVEL=debug
python test_mtls_connection.py
```

## 8. Security Considerations

- **Do not commit certificates to version control**
- Regularly rotate certificates (recommendation: quarterly)
- Use proper certificate management in production
- Restrict file permissions on certificate files
- Monitor for unauthorized access attempts