# Administrator Guide

This guide provides detailed information for RNA Lab Navigator administrators on system management, user administration, document ingestion, and maintenance tasks.

## System Administration

### Initial Setup

1. **Environment Configuration**
   - Configure environment variables in `.env` files
   - Set up database connections for PostgreSQL
   - Configure Weaviate vector database settings
   - Set OpenAI API keys and model preferences

2. **User Management**
   - Create initial administrator account
   - Set up authentication providers (local, LDAP, or SSO)
   - Configure role-based access controls

3. **Network Configuration**
   - Configure firewall rules for required services
   - Set up TLS certificates for secure communication
   - Configure proxy settings if operating behind a corporate firewall

### Deployment Options

RNA Lab Navigator supports several deployment configurations:

- **Local Development**: Use `docker-compose up` for local testing
- **Production (Railway)**: Deploy backend using `railway up`
- **Production (Vercel)**: Deploy frontend using `vercel --prod`
- **Hybrid Deployment**: Configure network isolation for sensitive environments

## User Management

### Managing Users

1. Access the administrator dashboard at `/admin`
2. Navigate to "User Management"
3. From here you can:
   - Create new user accounts
   - Assign roles and permissions
   - Disable inactive accounts
   - Reset passwords
   - Monitor user activity

### Role-Based Access Control

RNA Lab Navigator uses a role-based access system:

- **Admin**: Full access to all features and administrative functions
- **Lab Manager**: Can upload and manage documents, but cannot modify system settings
- **Researcher**: Standard access to search and view documents
- **Guest**: Limited access to public documents only

To modify roles:
1. Go to "User Management"
2. Select a user
3. Click "Edit Roles"
4. Assign appropriate roles
5. Save changes

## Document Management

### Document Ingestion

The system supports several ingestion methods:

#### 1. Single Document Upload
Use the web interface to upload individual documents:
- Navigate to the upload page
- Select document type
- Upload file
- Add metadata (author, year, keywords)
- Submit for processing

#### 2. Thesis Ingestion
For thesis documents, use the dedicated script:
```bash
python backend/api/ingestion/ingest_thesis.py PATH_TO_PDF "Author Name" YEAR
```

#### 3. Batch Ingestion
For multiple documents:
1. Prepare documents in a directory
2. Create a CSV metadata file
3. Run batch ingestion command:
```bash
python backend/api/ingestion/batch_ingest.py PATH_TO_DIR PATH_TO_METADATA.csv
```

#### 4. Automated Ingestion
Configure scheduled ingestion from repositories:
1. Go to "Admin Dashboard" > "Scheduled Tasks"
2. Configure sources (PubMed, bioRxiv, etc.)
3. Set keywords and filters
4. Define ingestion schedule

### Document Quality Management

1. **Validation**: Review automatically extracted metadata
2. **Enhancement**: Add missing keywords or classifications
3. **Deduplication**: Identify and merge duplicate documents
4. **Versioning**: Manage document updates and maintain version history

## System Monitoring

### Health Checks

Monitor system health through:
- Admin dashboard health indicators
- Prometheus metrics (if configured)
- Log analysis
- Database performance metrics

### Common Alerts

Configure alerts for:
- High server load
- Low disk space
- Database connection issues
- Ingestion pipeline failures
- Security incidents

### Performance Optimization

If performance degrades:
1. Check database indices
2. Verify Weaviate vector configuration
3. Adjust chunking parameters
4. Check network latency to OpenAI services
5. Review caching configuration

## Security Management

### Security Dashboard

The security dashboard provides:
- Overview of security incidents
- Failed login attempts
- Rate limit breaches
- IP blocking status
- Audit logs for sensitive operations

### Backup Management

Manage system backups:
1. Configure backup schedules
2. Verify backup integrity
3. Test restoration procedures
4. Configure off-site backup storage
5. Set retention policies

### mTLS Configuration

For secure communication with Weaviate:
1. Generate certificates using the provided scripts
2. Configure client and server certificates
3. Test secure communication
4. Rotate certificates according to your security policy

### Network Isolation

Configure LLM network isolation:
1. Navigate to "Admin Dashboard" > "Security Settings"
2. Select isolation level:
   - **None**: Direct connection to OpenAI APIs
   - **Proxy**: Route through authenticated proxy
   - **Air-gapped**: Use local Ollama models only
3. Test functionality at each isolation level

## Maintenance Tasks

### Routine Maintenance

Perform regularly:
- Database optimization
- Vector index optimization
- Log rotation
- Certificate renewal
- System updates
- Security patches

### Troubleshooting

Common issues and solutions:
- **Slow search responses**: Check network, OpenAI quota, or vector search parameters
- **Failed ingestion**: Verify document format, OCR quality, and chunking parameters
- **Authentication failures**: Check user database and authentication providers
- **Missing documents**: Check ingestion logs and search configuration

### System Updates

Follow this process for updates:
1. Backup all data
2. Update code from repository
3. Apply database migrations
4. Update configuration if needed
5. Test system functionality
6. Return to production

## Monitoring and Analytics

### Usage Statistics

Monitor:
- Daily active users
- Query volume
- Popular search terms
- Document access patterns
- Response times

### Quality Metrics

Track:
- User feedback ratings
- Answer precision
- Citation accuracy
- Query failure rate

### Resource Utilization

Monitor:
- OpenAI API usage and costs
- Database storage consumption
- Processing time for document ingestion
- Vector database performance

## Appendices

### Environment Variables Reference

Complete list of configuration options and environment variables.

### API Integration Guide

Documentation for programmatic access to the RNA Lab Navigator.

### Backup and Recovery Procedures

Detailed procedures for disaster recovery.

### Logging Configuration

Options for configuring log levels and storage.