"""
Custom User model for RNA Lab Navigator with GMP compliance features.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    """User roles with hierarchical permissions."""
    ADMIN = 'ADMIN', 'Administrator'
    PI = 'PI', 'Principal Investigator'
    SENIOR_RESEARCHER = 'SENIOR_RESEARCHER', 'Senior Researcher'
    RESEARCHER = 'RESEARCHER', 'Researcher'
    GUEST = 'GUEST', 'Guest Researcher'


class User(AbstractUser):
    """
    Custom User model with additional fields for GMP compliance.
    """
    # Override the related_name for groups and user_permissions to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='rna_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='rna_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    # Role-based access control
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.RESEARCHER,
        help_text="User's role determining their permissions"
    )
    
    # Professional information
    employee_id = models.CharField(
        max_length=50, 
        blank=True,
        null=True,
        help_text="CSIR-IGIB employee ID"
    )
    department = models.CharField(
        max_length=100,
        default="RNA Biology Lab",
        help_text="Department or research group"
    )
    phone = models.CharField(
        max_length=15, 
        blank=True,
        help_text="Contact phone number"
    )
    designation = models.CharField(
        max_length=100,
        blank=True,
        help_text="Official designation/title"
    )
    
    # Security fields
    last_password_change = models.DateTimeField(
        default=timezone.now,
        help_text="Last password change timestamp"
    )
    password_history = models.JSONField(
        default=list,
        help_text="History of password hashes for preventing reuse"
    )
    failed_login_attempts = models.IntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts"
    )
    account_locked_until = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Account lockout expiry time"
    )
    
    # Compliance fields
    terms_accepted_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When user accepted terms and conditions"
    )
    data_access_agreement_signed = models.BooleanField(
        default=False,
        help_text="Whether user signed data access agreement"
    )
    training_completed = models.JSONField(
        default=dict,
        help_text="Training modules completed with dates"
    )
    
    # Activity tracking
    last_activity = models.DateTimeField(
        auto_now=True,
        help_text="Last activity timestamp"
    )
    total_queries = models.IntegerField(
        default=0,
        help_text="Total number of queries made"
    )
    total_documents_uploaded = models.IntegerField(
        default=0,
        help_text="Total documents uploaded by user"
    )
    
    # Preferences
    notification_preferences = models.JSONField(
        default=dict,
        help_text="User notification preferences"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        help_text="Admin who created this user"
    )
    notes = models.TextField(
        blank=True,
        help_text="Administrative notes about the user"
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['role']),
            models.Index(fields=['email']),
            models.Index(fields=['-last_activity']),
        ]
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id})"
    
    @property
    def is_locked(self):
        """Check if account is currently locked."""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    @property
    def is_admin_or_pi(self):
        """Check if user has admin or PI role."""
        return self.role in [UserRole.ADMIN, UserRole.PI]
    
    @property
    def can_upload_documents(self):
        """Check if user can upload documents."""
        return self.role in [UserRole.ADMIN, UserRole.PI, UserRole.SENIOR_RESEARCHER]
    
    @property
    def can_delete_documents(self):
        """Check if user can delete documents."""
        return self.role in [UserRole.ADMIN, UserRole.PI]
    
    @property
    def can_view_all_sessions(self):
        """Check if user can view all chat sessions."""
        return self.role in [UserRole.ADMIN, UserRole.PI]
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role in [UserRole.ADMIN, UserRole.PI]
    
    def has_completed_training(self, module_name):
        """Check if user has completed a specific training module."""
        return module_name in self.training_completed
    
    def record_login_attempt(self, success=True):
        """Record login attempt and handle account locking."""
        if success:
            self.failed_login_attempts = 0
            self.last_login = timezone.now()
        else:
            self.failed_login_attempts += 1
            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.account_locked_until = timezone.now() + timezone.timedelta(hours=1)
        self.save()
    
    def check_password_history(self, raw_password):
        """Check if password was used before."""
        from django.contrib.auth.hashers import check_password
        for old_hash in self.password_history[-5:]:  # Check last 5 passwords
            if check_password(raw_password, old_hash):
                return False
        return True
    
    def set_password(self, raw_password):
        """Override to maintain password history."""
        # Store current password hash in history before changing
        if self.password:
            if not hasattr(self, 'password_history') or self.password_history is None:
                self.password_history = []
            self.password_history.append(self.password)
            # Keep only last 5 passwords
            self.password_history = self.password_history[-5:]
        
        super().set_password(raw_password)
        self.last_password_change = timezone.now()


class AuditLog(models.Model):
    """Audit log for tracking all user actions for GMP compliance."""
    
    ACTION_CHOICES = [
        # Authentication events
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGED', 'Password Changed'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('ACCOUNT_UNLOCKED', 'Account Unlocked'),
        
        # Data access events
        ('QUERY', 'Query Executed'),
        ('DOCUMENT_VIEWED', 'Document Viewed'),
        ('DOCUMENT_UPLOADED', 'Document Uploaded'),
        ('DOCUMENT_DELETED', 'Document Deleted'),
        ('DATA_EXPORTED', 'Data Exported'),
        
        # Permission events
        ('PERMISSION_DENIED', 'Permission Denied'),
        ('ROLE_CHANGED', 'User Role Changed'),
        
        # System events
        ('USER_CREATED', 'User Created'),
        ('USER_UPDATED', 'User Updated'),
        ('USER_DELETED', 'User Deleted'),
    ]
    
    # User information
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='audit_logs'
    )
    username = models.CharField(
        max_length=150,
        help_text="Username stored separately for audit trail integrity"
    )
    user_role = models.CharField(
        max_length=20,
        help_text="User role at the time of action"
    )
    
    # Action details
    action = models.CharField(
        max_length=50, 
        choices=ACTION_CHOICES
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    # Request information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Additional context
    resource = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Resource being accessed (e.g., document ID, query)"
    )
    details = models.JSONField(
        default=dict,
        help_text="Additional details about the action"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the action was successful"
    )
    
    # Compliance fields
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Session ID for tracking user sessions"
    )
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.username} - {self.action} - {self.timestamp}"