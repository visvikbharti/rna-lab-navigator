# RNA Lab Navigator - User Roles Documentation

## Overview

The RNA Lab Navigator implements a hierarchical role-based access control (RBAC) system designed to match the organizational structure of Dr. Chakraborty's RNA biology lab at CSIR-IGIB. This system ensures appropriate access levels for different lab members while maintaining data security and privacy.

## User Roles

### 1. **ADMIN** (System Administrator)
**Purpose**: Complete system control for technical administration

**Access Rights**:
- Full access to all system features and data
- User management (create, edit, delete users)
- System configuration and settings
- Access to all audit logs and analytics
- Can view and manage all documents
- Can access admin panel at `/admin`
- Can perform system maintenance tasks

**Intended For**: IT administrators, system maintainers

**Key Features**:
- User creation and management
- System monitoring dashboard
- Security configuration
- Backup and restore operations

### 2. **PI** (Principal Investigator)
**Purpose**: Lab head with oversight responsibilities

**Access Rights**:
- Access to admin panel for user management
- Can view all lab documents and research data
- Can approve new user registrations
- Can view lab-wide analytics and usage statistics
- Can manage document access permissions
- Can create and manage research projects

**Intended For**: Dr. Debojyoti Chakraborty and other PIs

**Key Features**:
- Lab member management
- Research oversight
- Document approval workflow
- Lab analytics dashboard

### 3. **SENIOR_RESEARCHER** (PhD Students, Post-docs)
**Purpose**: Advanced researchers with document upload privileges

**Access Rights**:
- Full search and query capabilities
- Can upload new documents (papers, protocols, theses)
- Can create and share document collections
- Can view their own usage analytics
- Can collaborate on shared projects
- Extended query limits (higher API usage allowed)

**Intended For**: PhD students, post-doctoral researchers

**Key Features**:
- Document upload interface
- Advanced search filters
- Collaboration tools
- Personal analytics dashboard

### 4. **RESEARCHER** (MSc Students, Junior Researchers)
**Purpose**: Regular lab members with standard access

**Access Rights**:
- Search and query existing documents
- Save favorite searches and documents
- Create personal notes on documents
- Standard query limits
- Can request document uploads (approved by seniors)
- Can participate in shared projects

**Intended For**: Master's students, research assistants, project staff

**Key Features**:
- Standard search interface
- Bookmark management
- Note-taking capabilities
- Request system for new documents

### 5. **GUEST** (Collaborators, Visitors)
**Purpose**: Limited access for external collaborators

**Access Rights**:
- Read-only access to approved documents
- Limited query quota (e.g., 10 queries per day)
- Cannot upload documents
- Cannot access sensitive lab data
- Time-limited access (auto-expires)

**Intended For**: Visiting researchers, external collaborators

**Key Features**:
- Restricted search interface
- Public document access only
- Session-based access
- No data persistence

## Role Hierarchy

```
ADMIN
  └── PI
      └── SENIOR_RESEARCHER
          └── RESEARCHER
              └── GUEST
```

Higher roles inherit all permissions of lower roles.

## Role-Based Features

### Document Access
- **ADMIN/PI**: All documents
- **SENIOR_RESEARCHER**: All public documents + ability to upload
- **RESEARCHER**: All public documents + request uploads
- **GUEST**: Only explicitly shared documents

### Query Limits (per day)
- **ADMIN**: Unlimited
- **PI**: 500 queries
- **SENIOR_RESEARCHER**: 200 queries
- **RESEARCHER**: 100 queries
- **GUEST**: 10 queries

### Analytics Access
- **ADMIN**: System-wide analytics
- **PI**: Lab-wide analytics
- **SENIOR_RESEARCHER**: Personal + project analytics
- **RESEARCHER**: Personal analytics only
- **GUEST**: No analytics access

## Security Considerations

1. **Authentication**: All users must authenticate with username/password
2. **Session Management**: Sessions expire after 24 hours of inactivity
3. **Audit Trail**: All actions are logged with user, timestamp, and IP
4. **Data Privacy**: Users can only see their own personal data unless explicitly shared
5. **Document Security**: Sensitive documents can be restricted by role

## Role Assignment Process

1. New users register with basic information
2. Default role is set to RESEARCHER
3. PI or ADMIN can upgrade roles as needed
4. Role changes are logged in audit trail
5. Email notification sent on role change

## Best Practices

1. **Principle of Least Privilege**: Assign the minimum role necessary
2. **Regular Reviews**: PI should review user roles quarterly
3. **Guest Cleanup**: Guest accounts auto-expire after 30 days
4. **Document Classification**: Mark sensitive documents appropriately
5. **Training**: Ensure users understand their role capabilities

## Technical Implementation

The role system is implemented using Django's built-in permissions framework with custom extensions:

```python
class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrator'
    PI = 'PI', 'Principal Investigator'
    SENIOR_RESEARCHER = 'SENIOR_RESEARCHER', 'Senior Researcher'
    RESEARCHER = 'RESEARCHER', 'Researcher'
    GUEST = 'GUEST', 'Guest'
```

Permissions are checked at both the view level (using decorators) and the model level (using Django's permission system).

## Future Enhancements

1. **Dynamic Roles**: Create custom roles for specific projects
2. **External Authentication**: Integration with institutional SSO
3. **Fine-grained Permissions**: Document-level access control
4. **Delegation**: Allow PIs to delegate specific permissions
5. **API Access**: Role-based API keys for programmatic access

---

*This document should be reviewed and updated as the system evolves and new requirements emerge.*