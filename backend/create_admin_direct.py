#!/usr/bin/env python
"""
Direct admin creation for PythonAnywhere - bypasses settings issues
"""
import os
import sys
import django
from django.conf import settings

# Configure Django settings directly
settings.configure(
    DEBUG=True,
    SECRET_KEY='django-insecure-bm6=6q7v3uh@o0e&_06(nq*!i*3l@p=o%j9a0tja+j3z+8c#e4',
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'rnalab$rna_lab_db',
            'USER': 'super',
            'PASSWORD': 'qwerty121',
            'HOST': 'rnalab-4669.postgres.pythonanywhere-services.com',
            'PORT': '14669',
        }
    },
    INSTALLED_APPS=[
        'django.contrib.auth',
        'django.contrib.contenttypes',
    ],
    USE_TZ=True,
)

# Setup Django
django.setup()

# Now create the superuser
from django.contrib.auth.models import User

try:
    # First, let's check if the table exists
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'auth_user')")
        table_exists = cursor.fetchone()[0]
        
    if table_exists:
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
    else:
        print("❌ The auth_user table doesn't exist. Run migrations first!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()