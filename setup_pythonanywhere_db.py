#!/usr/bin/env python3
"""
PythonAnywhere Database Setup Helper
"""

import os
import sys

print("=== PythonAnywhere Database Setup ===\n")

print("1. First, check your database details in the Databases tab:")
print("   - Your database name should be: rnalab$rna_lab_db")
print("   - Your username is: rnalab")
print("   - Your host should be: rnalab-postgres.postgres.pythonanywhere-services.com")
print("   - Note: The host format is: username-postgres.postgres.pythonanywhere-services.com")

print("\n2. Set these environment variables in the Web tab:")
print("   SECRET_KEY = <generate a long random string>")
print("   DB_PASSWORD = <your PostgreSQL password from Databases tab>")
print("   OPENAI_API_KEY = <your OpenAI API key>")

print("\n3. To generate a SECRET_KEY, run this:")
print("   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'")

print("\n4. Current database configuration:")
db_host = "rnalab.postgres.pythonanywhere-services.com"
correct_host = "rnalab-postgres.postgres.pythonanywhere-services.com"

print(f"   Current host: {db_host}")
print(f"   Should be: {correct_host}")

print("\n5. To test database connection manually:")
print("""
import psycopg2
conn = psycopg2.connect(
    host='rnalab-postgres.postgres.pythonanywhere-services.com',
    database='rnalab$rna_lab_db',
    user='rnalab',
    password='your-password-here'
)
print('Connection successful!')
conn.close()
""")

print("\n6. Quick fix - Update the host in settings_pythonanywhere.py:")
print("   Change:")
print("   'HOST': 'rnalab.postgres.pythonanywhere-services.com',")
print("   To:")
print("   'HOST': 'rnalab-postgres.postgres.pythonanywhere-services.com',")

print("\n7. Alternative - Use SQLite for testing:")
print("   If PostgreSQL is not set up yet, you can temporarily use SQLite")
print("   by commenting out the DATABASES section in settings_pythonanywhere.py")

print("\n=== Next Steps ===")
print("1. Set the environment variables in PythonAnywhere Web tab")
print("2. Fix the database host in settings_pythonanywhere.py")
print("3. Reload your web app")
print("4. Run: python manage.py migrate")
print("5. Run: python manage.py createsuperuser")
print("6. Test with: python test_api_endpoints.py")