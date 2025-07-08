# This is the complete WSGI configuration for PythonAnywhere
# Replace the contents of /var/www/rnalab_pythonanywhere_com_wsgi.py with this file

import os
import sys

# Add these environment variables BEFORE importing Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'rna_backend.settings_pythonanywhere'
os.environ['SECRET_KEY'] = 'django-insecure-bm6=6q7v3uh@o0e&_06(nq*!i*3l@p=o%j9a0tja+j3z+8c#e4'
os.environ['DB_PASSWORD'] = 'qwerty121'
os.environ['DB_PORT'] = '14669'
os.environ['OPENAI_API_KEY'] = 'your-openai-api-key-here'  # Add your actual OpenAI API key
os.environ['DEBUG'] = 'False'  # Important: Set to False in production
os.environ['ALLOWED_HOSTS'] = 'rnalab.pythonanywhere.com'

# Add your project directory to the sys.path
project_home = '/home/rnalab/rna-lab-navigator/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import Django and get WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Optional: Add static file serving (PythonAnywhere usually handles this automatically)
# from django.contrib.staticfiles.handlers import StaticFilesHandler
# application = StaticFilesHandler(application)