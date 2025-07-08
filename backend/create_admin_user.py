#!/usr/bin/env python
"""
Create admin superuser with proper database configuration for PythonAnywhere
"""
import os
import sys

# Set all environment variables BEFORE importing Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'rna_backend.settings_pythonanywhere'
os.environ['SECRET_KEY'] = 'django-insecure-bm6=6q7v3uh@o0e&_06(nq*!i*3l@p=o%j9a0tja+j3z+8c#e4'
os.environ['DEBUG'] = 'True'
os.environ['ALLOWED_HOSTS'] = 'rnalab.pythonanywhere.com,localhost,127.0.0.1'

# PostgreSQL Database settings - CRITICAL!
os.environ['DB_ENGINE'] = 'django.db.backends.postgresql'
os.environ['DB_NAME'] = 'rnalab$rna_lab_db'
os.environ['DB_USER'] = 'super'
os.environ['DB_PASSWORD'] = 'qwerty121'
os.environ['DB_HOST'] = 'rnalab-2025.postgres.pythonanywhere-services.com'
os.environ['DB_PORT'] = '12025'

# Other settings
os.environ['WEAVIATE_URL'] = 'http://localhost:8080'
os.environ['OPENAI_API_KEY'] = 'sk-proj-your-actual-key'
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['CORS_ALLOWED_ORIGINS'] = 'http://localhost:3000,http://localhost:5173,https://rna-lab-navigator.vercel.app'

# Now import Django
import django
django.setup()

# Import User model
from django.contrib.auth.models import User

# Create superuser
try:
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser(
            username='admin',
            email='admin@rnalab.com',
            password='GODisone@1'
        )
        print("✅ Admin superuser created successfully!")
        print("   Username: admin")
        print("   Password: GODisone@1")
    else:
        print("ℹ️  Admin user already exists")
except Exception as e:
    print(f"❌ Error creating superuser: {e}")
    print("\nDEBUG: Current database settings:")
    from django.conf import settings
    db_settings = settings.DATABASES['default']
    print(f"  ENGINE: {db_settings.get('ENGINE')}")
    print(f"  NAME: {db_settings.get('NAME')}")
    print(f"  HOST: {db_settings.get('HOST')}")
    print(f"  PORT: {db_settings.get('PORT')}")
    print(f"  USER: {db_settings.get('USER')}")