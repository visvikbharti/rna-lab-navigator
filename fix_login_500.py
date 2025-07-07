#!/usr/bin/env python3
"""
Quick fix script for login 500 error on PythonAnywhere
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, '/home/rnalab/rna-lab-navigator/backend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings_pythonanywhere')

print("=== Fixing Login 500 Error ===\n")

# Setup Django
try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    print("\nMake sure you're in the virtual environment!")
    sys.exit(1)

# 1. Run migrations
print("\n1. Running migrations...")
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    print("✓ Migrations complete")
except Exception as e:
    print(f"✗ Migration error: {e}")

# 2. Collect static files
print("\n2. Collecting static files...")
try:
    call_command('collectstatic', interactive=False, verbosity=0)
    print("✓ Static files collected")
except Exception as e:
    print(f"✗ Static files error: {e}")

# 3. Create admin user if doesn't exist
print("\n3. Checking admin user...")
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        print("Creating admin user...")
        User.objects.create_superuser(
            username='admin',
            email='admin@rnalab.com',
            password='GODisone@1'
        )
        print("✓ Admin user created")
    else:
        print("✓ Admin user already exists")
        # Reset password just in case
        user = User.objects.get(username='admin')
        user.set_password('GODisone@1')
        user.save()
        print("✓ Admin password reset")
except Exception as e:
    print(f"✗ User creation error: {e}")

# 4. Test the login
print("\n4. Testing login functionality...")
try:
    from rest_framework_simplejwt.tokens import RefreshToken
    from django.contrib.auth import authenticate
    
    user = authenticate(username='admin', password='GODisone@1')
    if user:
        refresh = RefreshToken.for_user(user)
        print("✓ Login test successful")
        print(f"  Access token (first 20 chars): {str(refresh.access_token)[:20]}...")
    else:
        print("✗ Authentication failed")
except Exception as e:
    print(f"✗ Login test error: {e}")

# 5. Check for common issues
print("\n5. Checking common issues...")

# Check if api_auth tables exist
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'api_auth_%'
        """)
        tables = cursor.fetchall()
        print(f"✓ Found {len(tables)} api_auth tables")
        for table in tables:
            print(f"  - {table[0]}")
except Exception as e:
    print(f"✗ Table check error: {e}")

print("\n=== Fix Complete ===")
print("\nNext steps:")
print("1. Check if the error persists")
print("2. If yes, check ~/rna-lab-navigator/backend/error.log")
print("3. Reload the web app from PythonAnywhere dashboard")
print("4. Test again with: python test_api_endpoints.py")