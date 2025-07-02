#!/usr/bin/env python
"""
Direct test of authentication without going through the web server
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from django.contrib.auth import authenticate
from api.auth.models import User

def test_auth():
    print("Testing authentication...")
    
    # List all users
    users = User.objects.all()
    print(f"\nFound {users.count()} users:")
    for user in users:
        print(f"  - {user.username} (is_superuser: {user.is_superuser})")
    
    # Test authentication
    username = 'admin'
    password = 'admin123'
    
    print(f"\nTesting login with {username}/{password}")
    
    # Create a mock request for Axes
    from django.http import HttpRequest
    request = HttpRequest()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    
    user = authenticate(request=request, username=username, password=password)
    
    if user:
        print(f"✓ Authentication successful! User: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Is active: {user.is_active}")
        print(f"  Is superuser: {user.is_superuser}")
    else:
        print("✗ Authentication failed!")
        
        # Check if user exists
        try:
            user = User.objects.get(username=username)
            print(f"  User '{username}' exists but password is incorrect")
            # Try to set the password again
            user.set_password(password)
            user.save()
            print(f"  Password reset for user '{username}'")
            
            # Test again
            user = authenticate(request=request, username=username, password=password)
            if user:
                print("  ✓ Authentication successful after password reset!")
            else:
                print("  ✗ Still failing after password reset")
        except User.DoesNotExist:
            print(f"  User '{username}' does not exist")

if __name__ == "__main__":
    test_auth()