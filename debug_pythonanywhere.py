#!/usr/bin/env python3
"""
Debug script for PythonAnywhere deployment issues
Run this on PythonAnywhere to diagnose problems
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, '/home/rnalab/rna-lab-navigator/backend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings_pythonanywhere')

print("=== RNA Lab Navigator Debug Script ===\n")

# 1. Check environment variables
print("1. Environment Variables:")
important_vars = [
    'DJANGO_SETTINGS_MODULE',
    'SECRET_KEY',
    'DB_PASSWORD',
    'DB_PORT',
    'OPENAI_API_KEY',
    'WEAVIATE_URL'
]

for var in important_vars:
    value = os.environ.get(var, 'NOT SET')
    if var in ['SECRET_KEY', 'DB_PASSWORD', 'OPENAI_API_KEY']:
        # Mask sensitive values
        if value != 'NOT SET':
            value = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
    print(f"   {var}: {value}")

print("\n2. Django Setup:")
try:
    django.setup()
    print("   ✓ Django setup successful")
except Exception as e:
    print(f"   ✗ Django setup failed: {e}")
    sys.exit(1)

print("\n3. Database Connection:")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("   ✓ Database connection successful")
except Exception as e:
    print(f"   ✗ Database connection failed: {e}")

print("\n4. User Model:")
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_count = User.objects.count()
    print(f"   ✓ User model accessible, {user_count} users in database")
    
    # Check if admin user exists
    admin_exists = User.objects.filter(username='admin').exists()
    print(f"   Admin user exists: {admin_exists}")
except Exception as e:
    print(f"   ✗ User model error: {e}")

print("\n5. Installed Apps:")
try:
    from django.conf import settings
    auth_apps = [app for app in settings.INSTALLED_APPS if 'auth' in app or 'jwt' in app]
    for app in auth_apps:
        print(f"   - {app}")
except Exception as e:
    print(f"   ✗ Error accessing settings: {e}")

print("\n6. Middleware:")
try:
    middleware = settings.MIDDLEWARE
    important_middleware = [m for m in middleware if any(x in m for x in ['cors', 'auth', 'csrf'])]
    for m in important_middleware:
        print(f"   - {m}")
except Exception as e:
    print(f"   ✗ Error accessing middleware: {e}")

print("\n7. CORS Settings:")
try:
    print(f"   CORS_ALLOWED_ORIGINS: {len(settings.CORS_ALLOWED_ORIGINS)} origins")
    print(f"   CORS_ALLOW_CREDENTIALS: {settings.CORS_ALLOW_CREDENTIALS}")
    if hasattr(settings, 'CORS_ALLOWED_ORIGIN_REGEXES'):
        print(f"   CORS_ALLOWED_ORIGIN_REGEXES: {len(settings.CORS_ALLOWED_ORIGIN_REGEXES)} patterns")
except Exception as e:
    print(f"   ✗ Error accessing CORS settings: {e}")

print("\n8. Static Files:")
try:
    print(f"   STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"   STATIC_URL: {settings.STATIC_URL}")
    static_exists = os.path.exists(settings.STATIC_ROOT)
    print(f"   Static directory exists: {static_exists}")
except Exception as e:
    print(f"   ✗ Error with static files: {e}")

print("\n9. Test Import of Auth Views:")
try:
    from api.auth.views import CustomTokenObtainPairView
    print("   ✓ Auth views importable")
except Exception as e:
    print(f"   ✗ Auth views import error: {e}")

print("\n10. Check Migrations:")
try:
    from django.core.management import call_command
    from io import StringIO
    out = StringIO()
    call_command('showmigrations', '--plan', stdout=out)
    migrations = out.getvalue()
    # Count applied migrations
    applied = migrations.count('[X]')
    pending = migrations.count('[ ]')
    print(f"   Applied migrations: {applied}")
    print(f"   Pending migrations: {pending}")
    if pending > 0:
        print("   ⚠️  You need to run: python manage.py migrate")
except Exception as e:
    print(f"   ✗ Migration check error: {e}")

print("\n=== Debug Complete ===")
print("\nSuggested fixes:")
if os.environ.get('SECRET_KEY') == 'NOT SET':
    print("1. Set SECRET_KEY in PythonAnywhere environment variables")
if os.environ.get('DB_PASSWORD') == 'NOT SET':
    print("2. Set DB_PASSWORD in PythonAnywhere environment variables")
print("3. Check the error log at: ~/rna-lab-navigator/backend/error.log")
print("4. Reload the web app after any changes")