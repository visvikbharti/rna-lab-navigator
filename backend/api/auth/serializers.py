"""
Serializers for authentication with GMP compliance.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User, AuditLog, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with additional user data."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['employee_id'] = user.employee_id
        token['department'] = user.department
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add extra responses here
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'role': self.user.role,
                'department': self.user.department,
                'employee_id': self.user.employee_id,
                'is_locked': self.user.is_locked,
                'terms_accepted': bool(self.user.terms_accepted_at),
                'data_access_agreement_signed': self.user.data_access_agreement_signed,
            }
        })
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'employee_id', 'department', 'phone', 'designation', 'role',
            'is_active', 'is_locked', 'terms_accepted_at', 
            'data_access_agreement_signed', 'last_activity', 'date_joined',
            'total_queries', 'total_documents_uploaded', 'notification_preferences'
        ]
        read_only_fields = [
            'id', 'username', 'is_locked', 'last_activity', 'date_joined',
            'total_queries', 'total_documents_uploaded'
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'employee_id', 'department',
            'phone', 'designation', 'role'
        ]
        
    def validate_employee_id(self, value):
        """Validate employee ID is unique."""
        if User.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("Employee ID already exists.")
        return value
    
    def validate(self, attrs):
        """Validate passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        
        return attrs
    
    def create(self, validated_data):
        """Create user with validated data."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Create user
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        """Validate new passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "New password fields didn't match."})
        
        # Validate password strength
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})
        
        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs."""
    username = serializers.CharField(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'username', 'user_role', 'action', 'action_display',
            'timestamp', 'ip_address', 'user_agent', 'resource',
            'details', 'success', 'session_id'
        ]
        read_only_fields = fields  # All fields are read-only for audit logs