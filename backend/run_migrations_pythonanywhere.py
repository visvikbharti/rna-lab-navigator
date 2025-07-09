#!/usr/bin/env python
"""
Run Django migrations with PythonAnywhere database configuration
"""
import os
import sys

# Add backend to path
sys.path.insert(0, '/home/rnalab/rna-lab-navigator/backend')

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'rna_backend.settings_pythonanywhere'
os.environ['DB_PASSWORD'] = 'qwerty121'
os.environ['DB_PORT'] = '14669'
os.environ['SECRET_KEY'] = 'django-insecure-bm6=6q7v3uh@o0e&_06(nq*!i*3l@p=o%j9a0tja+j3z+8c#e4'

# Import Django
import django
django.setup()

# Run migrations
from django.core.management import execute_from_command_line

print("🔄 Running migrations with PythonAnywhere settings...")
execute_from_command_line(['manage.py', 'migrate'])
print("✅ Migrations complete!")