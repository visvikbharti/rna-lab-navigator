# RNA Lab Navigator - Authentication System Design
**Created**: June 27, 2025, 14:45 IST  
**Author**: Vishal Bharti & Claude Code Assistant  
**Status**: Ready for Implementation

---

## 🎯 Objectives

1. **GMP Compliance**: Meet Good Manufacturing Practice standards
2. **Security**: Protect sensitive research data
3. **Usability**: Simple login process for researchers
4. **Auditability**: Track all access and actions
5. **Scalability**: Support 50+ concurrent users

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Login Page  │  │ Auth Context │  │ Protected     │  │
│  │             │  │ & Provider   │  │ Routes        │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ JWT Tokens
┌────────────────────────▼────────────────────────────────┐
│                   Backend (Django)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Auth Views  │  │ JWT Handler  │  │ Permissions   │  │
│  │ (Login API) │  │ Middleware   │  │ Decorators    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │Postgres │
                    │ Users   │
                    └─────────┘
```

---

## 👥 User Roles & Permissions

### Role Hierarchy

```python
class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrator'
    PI = 'PI', 'Principal Investigator'  # Dr. Chakraborty
    SENIOR_RESEARCHER = 'SENIOR_RESEARCHER', 'Senior Researcher'
    RESEARCHER = 'RESEARCHER', 'Researcher'
    GUEST = 'GUEST', 'Guest Researcher'
```

### Permission Matrix

| Action | Admin | PI | Senior | Researcher | Guest |
|--------|-------|-----|---------|------------|-------|
| View documents | ✅ | ✅ | ✅ | ✅ | ✅* |
| Query system | ✅ | ✅ | ✅ | ✅ | ✅* |
| Upload documents | ✅ | ✅ | ✅ | ❌ | ❌ |
| Delete documents | ✅ | ✅ | ❌ | ❌ | ❌ |
| View all sessions | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage users | ✅ | ✅ | ❌ | ❌ | ❌ |
| View audit logs | ✅ | ✅ | ✅ | ❌ | ❌ |
| Export data | ✅ | ✅ | ✅ | ✅ | ❌ |

*Guest access limited to public documents only

---

## 🔑 Technical Implementation

### 1. User Model Extension

```python
# backend/api/auth/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.RESEARCHER
    )
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    
    # Security fields
    last_password_change = models.DateTimeField(auto_now_add=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Compliance fields
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    data_access_agreement_signed = models.BooleanField(default=False)
    
    # Activity tracking
    last_activity = models.DateTimeField(auto_now=True)
    total_queries = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['role']),
        ]
```

### 2. JWT Configuration

```python
# backend/rna_backend/settings.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    
    # Custom claims
    'TOKEN_OBTAIN_SERIALIZER': 'api.auth.serializers.CustomTokenObtainPairSerializer',
}

# Session configuration
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

### 3. Authentication Views

```python
# backend/api/auth/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer
from api.audit.utils import log_auth_event

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Check for locked account
        username = request.data.get('username')
        try:
            user = User.objects.get(username=username)
            if user.account_locked_until and user.account_locked_until > timezone.now():
                log_auth_event('LOGIN_BLOCKED', username, request)
                return Response(
                    {'error': 'Account is locked. Please contact administrator.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except User.DoesNotExist:
            pass
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Successful login
            user = User.objects.get(username=username)
            user.failed_login_attempts = 0
            user.save()
            
            log_auth_event('LOGIN_SUCCESS', user, request)
            
            # Add user info to response
            response.data['user'] = UserSerializer(user).data
        else:
            # Failed login
            try:
                user = User.objects.get(username=username)
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.account_locked_until = timezone.now() + timedelta(hours=1)
                    log_auth_event('ACCOUNT_LOCKED', user, request)
                
                user.save()
            except User.DoesNotExist:
                pass
            
            log_auth_event('LOGIN_FAILED', username, request)
        
        return response
```

### 4. Permission System

```python
# backend/api/auth/permissions.py
from rest_framework import permissions

class RoleBasedPermission(permissions.BasePermission):
    """
    Custom permission to check user roles
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get required roles from view
        allowed_roles = getattr(view, 'allowed_roles', [])
        
        # Admin and PI always have access
        if request.user.role in ['ADMIN', 'PI']:
            return True
        
        # Check if user's role is allowed
        return request.user.role in allowed_roles

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Only allow owners of an object or admins to access it
    """
    def has_object_permission(self, request, view, obj):
        # Admin and PI can access anything
        if request.user.role in ['ADMIN', 'PI']:
            return True
        
        # Check if user owns the object
        return obj.user == request.user
```

### 5. Audit Trail

```python
# backend/api/audit/models.py
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('LOGOUT', 'Logout'),
        ('QUERY', 'Query Executed'),
        ('UPLOAD', 'Document Uploaded'),
        ('DELETE', 'Document Deleted'),
        ('EXPORT', 'Data Exported'),
        ('PERMISSION_DENIED', 'Permission Denied'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=150)  # Store even if user deleted
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Additional context
    resource = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict)
    success = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
```

---

## 🎨 Frontend Implementation

### 1. Auth Context

```javascript
// frontend/src/contexts/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import { authApi } from '../api/auth';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tokens, setTokens] = useState({
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token')
  });

  // Check token validity on mount
  useEffect(() => {
    if (tokens.access) {
      validateToken();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    try {
      const response = await authApi.login(username, password);
      const { access, refresh, user } = response.data;
      
      // Store tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      setTokens({ access, refresh });
      setUser(user);
      
      // Set default auth header
      authApi.setAuthHeader(access);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed' 
      };
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local data
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setTokens({ access: null, refresh: null });
      setUser(null);
      authApi.clearAuthHeader();
    }
  };

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    loading,
    hasRole: (role) => user?.role === role || user?.role === 'ADMIN',
    canAccess: (resource) => checkPermission(user, resource)
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
```

### 2. Protected Routes

```javascript
// frontend/src/components/ProtectedRoute.jsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const ProtectedRoute = ({ 
  children, 
  requiredRoles = [],
  requiredPermissions = [] 
}) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check roles
  if (requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.includes(user.role) || 
                           user.role === 'ADMIN';
    if (!hasRequiredRole) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  // Check permissions
  if (requiredPermissions.length > 0) {
    const hasAllPermissions = requiredPermissions.every(
      permission => user.permissions?.includes(permission)
    );
    if (!hasAllPermissions) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return children;
};
```

---

## 🔒 Security Measures

### 1. Password Policy
- Minimum 12 characters
- Must include: uppercase, lowercase, number, special character
- Cannot reuse last 5 passwords
- Expires every 90 days
- Account lockout after 5 failed attempts

### 2. Session Security
- JWT tokens expire after 8 hours
- Refresh tokens expire after 7 days
- Session timeout after 30 minutes of inactivity
- Logout invalidates all tokens

### 3. Additional Security
- HTTPS only in production
- CSRF protection enabled
- Rate limiting on auth endpoints
- IP whitelisting (optional)
- Multi-factor authentication (Phase 2)

---

## 📊 Monitoring & Alerts

### Key Metrics
1. Failed login attempts per user
2. Unusual access patterns
3. Permission denied events
4. Session duration statistics
5. API usage by role

### Alerts
- 5+ failed login attempts → Email to admin
- Access from new IP → Email to user
- Sensitive data export → Log and notify PI
- Account locked → Email to user and admin

---

## 🧪 Testing Strategy

### Unit Tests
- User model validations
- Permission checks
- JWT token generation/validation
- Password policy enforcement

### Integration Tests
- Login flow end-to-end
- Token refresh mechanism
- Role-based access control
- Audit logging

### Security Tests
- SQL injection attempts
- XSS prevention
- CSRF protection
- Rate limiting

---

## 📝 Implementation Checklist

### Day 1 - Backend
- [ ] Create custom User model
- [ ] Set up JWT authentication
- [ ] Implement login/logout views
- [ ] Add permission classes
- [ ] Create audit log model
- [ ] Add authentication middleware

### Day 2 - Frontend
- [ ] Create login page UI
- [ ] Implement auth context
- [ ] Add protected routes
- [ ] Create user profile page
- [ ] Add logout functionality
- [ ] Handle token refresh

### Day 3 - Testing & Documentation
- [ ] Write unit tests
- [ ] Create integration tests
- [ ] Document API endpoints
- [ ] Create user guide
- [ ] Set up monitoring
- [ ] Deploy to staging

---

## 🚀 Future Enhancements

### Phase 2 (Month 2)
- Multi-factor authentication
- SSO integration
- Biometric authentication
- Advanced threat detection

### Phase 3 (Month 3)
- External collaborator access
- Temporary access tokens
- API key management
- OAuth2 provider

---

**Document Version**: 1.0  
**Review Date**: June 28, 2025  
**Approved By**: Pending

---

*This design ensures GMP compliance while maintaining usability for researchers.*