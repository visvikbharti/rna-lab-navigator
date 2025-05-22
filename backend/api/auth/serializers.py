"""
Authentication serializers for the RNA Lab Navigator.
Provides serializers for user registration, profile management, and password management.
"""

import re
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate(self, data):
        """
        Validate that the passwords match.
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords don't match"})
        return data
    
    def create(self, validated_data):
        """
        Create and return a new user instance.
        """
        # Remove password_confirm from validated data
        validated_data.pop('password_confirm')
        
        # Create user with encrypted password
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        
        user.set_password(validated_data['password'])
        user.save()
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile management.
    """
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        required=False
    )
    
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'date_joined', 'last_login', 'roles', 'permissions')
        read_only_fields = ('id', 'username', 'date_joined', 'last_login', 
                           'roles', 'permissions')
    
    def get_roles(self, obj):
        from .models import UserRole
        roles = UserRole.objects.filter(user=obj)
        return [{'role': role.role, 'name': role.get_role_display()} for role in roles]
    
    def get_permissions(self, obj):
        from .models import UserPermission
        permissions = UserPermission.objects.filter(user=obj)
        return [{'permission': perm.permission, 'name': perm.get_permission_display()} 
                for perm in permissions]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        """
        Validate that the current password is correct.
        """
        user = self.context.get('user')
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate(self, data):
        """
        Validate that the new passwords match.
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords don't match."})
        
        # Check that new password is not the same as the current password
        if data['current_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "New password must be different from current password."})
        
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset.
    """
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset.
    """
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, data):
        """
        Validate that the new passwords match.
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords don't match."})
        
        # Validate UID is valid base64
        try:
            user_id = force_str(urlsafe_base64_decode(data['uid']))
            # Just check if decoding works, don't need the result here
        except (TypeError, ValueError, OverflowError):
            raise serializers.ValidationError({"uid": "Invalid user ID encoding."})
        
        return data