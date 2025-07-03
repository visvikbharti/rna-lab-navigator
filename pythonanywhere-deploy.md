# Deploy RNA Lab Navigator on PythonAnywhere (FREE - No Card Required!)

This will get your app running TODAY for beta testing with your 21 lab members.

## Step 1: Create PythonAnywhere Account

1. Go to: https://www.pythonanywhere.com
2. Click "Start running Python online in less than a minute!"
3. Create username (e.g., `rnalab` or `igiblab`)
4. Use your institute email
5. **No credit card required!**

## Step 2: Create Web App

1. After login, go to "Web" tab
2. Click "Add a new web app"
3. Choose:
   - Select "Manual configuration"
   - Choose "Python 3.9"
4. Note your URL: `https://yourusername.pythonanywhere.com`

## Step 3: Set Up Database

PythonAnywhere gives you free PostgreSQL! In "Databases" tab:
1. Initialize PostgreSQL
2. Create database: `rna_lab_db`
3. Note credentials:
   - Username: `yourusername$rna_lab_db`
   - Host: `yourusername.postgres.pythonanywhere-services.com`
   - Port: `10124` (specific to your account)

## Step 4: Upload Code

In "Consoles" tab, start a Bash console:

```bash
# Clone your repository
git clone https://github.com/visvikbharti/rna-lab-navigator.git
cd rna-lab-navigator/backend

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install django djangorestframework django-cors-headers
pip install psycopg2-binary djangorestframework-simplejwt
pip install openai langchain pandas numpy
pip install whitenoise gunicorn

# Create production settings
cp rna_backend/settings.py rna_backend/settings_pythonanywhere.py
```

## Step 5: Configure Settings

Edit `rna_backend/settings_pythonanywhere.py`:

```python
import os
from .settings import *

# PythonAnywhere specific
ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
DEBUG = False

# Database - use PythonAnywhere's PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'yourusername$rna_lab_db',
        'USER': 'yourusername',
        'PASSWORD': 'your-db-password',  # Set in Databases tab
        'HOST': 'yourusername.postgres.pythonanywhere-services.com',
        'PORT': '10124',  # Your specific port
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = '/home/yourusername/rna-lab-navigator/backend/static'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/yourusername/rna-lab-navigator/backend/media'

# Security
SECRET_KEY = 'generate-a-long-random-string-here'

# CORS - allow your Vercel frontend
CORS_ALLOWED_ORIGINS = [
    'https://rna-lab-navigator.vercel.app',
]

# OpenAI
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')  # Set in environment variables

# Disable features that need more resources
CELERY_TASK_ALWAYS_EAGER = True  # No Celery on free tier
USE_REDIS = False  # No Redis on free tier

# Simplified Weaviate alternative
USE_SIMPLE_SEARCH = True  # We'll implement a simple search
```

## Step 6: Configure WSGI

In Web tab, configure:
- **Source code**: `/home/yourusername/rna-lab-navigator/backend`
- **Working directory**: `/home/yourusername/rna-lab-navigator/backend`
- **WSGI file**: Click to edit and replace with:

```python
import os
import sys

path = '/home/yourusername/rna-lab-navigator/backend'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'rna_backend.settings_pythonanywhere'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Step 7: Static Files

In Web tab, set up static files mapping:
- URL: `/static/`
- Directory: `/home/yourusername/rna-lab-navigator/backend/static`

## Step 8: Initialize Database

In Bash console:
```bash
cd ~/rna-lab-navigator/backend
source venv/bin/activate

# Set environment variable
export DJANGO_SETTINGS_MODULE=rna_backend.settings_pythonanywhere

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Username: admin
# Email: admin@igib.res.in
# Password: choose a secure password

# Collect static files
python manage.py collectstatic --noinput
```

## Step 9: Simplified Search (No Weaviate)

Create `backend/api/search/simple_search.py`:
```python
from django.db.models import Q
from api.ingestion.models import Document, DocumentChunk

class SimpleSearchEngine:
    """Fallback search when Weaviate is not available"""
    
    def search(self, query, limit=5):
        # Simple keyword search
        chunks = DocumentChunk.objects.filter(
            Q(content__icontains=query) |
            Q(document__title__icontains=query)
        )[:limit]
        
        results = []
        for chunk in chunks:
            results.append({
                'content': chunk.content,
                'metadata': {
                    'source': chunk.document.title,
                    'page': chunk.metadata.get('page', 'N/A'),
                    'chunk_index': chunk.chunk_index,
                },
                'score': 0.8  # Dummy score
            })
        
        return results
```

## Step 10: Update Frontend

Update your frontend `.env.production`:
```
VITE_API_BASE_URL=https://yourusername.pythonanywhere.com/api
```

Then redeploy:
```bash
cd frontend
vercel --prod
```

## Step 11: Test Your Deployment

1. Visit: `https://yourusername.pythonanywhere.com/admin`
2. Login with your superuser credentials
3. Visit your Vercel frontend
4. Test login and search functionality

## Limitations & Workarounds

### Free Tier Limits:
- **CPU seconds**: 100/day (resets at midnight UTC)
- **Bandwidth**: 10GB/month
- **No background tasks**: Can't use Celery
- **No WebSockets**: Real-time features disabled

### Workarounds:
1. **For Background Tasks**: Use cron jobs (Scheduled tasks tab)
2. **For Real-time**: Use polling instead of WebSockets
3. **For Heavy Processing**: Process during off-hours

## Performance Tips

1. **Enable WhiteNoise** for static files
2. **Use database indexing** for search fields
3. **Implement caching** with Django's cache framework
4. **Optimize queries** with select_related/prefetch_related

## Next Steps

Once running on PythonAnywhere:
1. Share URL with lab members for testing
2. Collect feedback
3. Apply for cloud credits for production deployment
4. Work with IT for institutional hosting

## Troubleshooting

### "Something went wrong :-("
- Check error log in Web tab
- Common issues: import errors, wrong Python version

### Database connection errors
- Verify credentials in Databases tab
- Check host and port are correct

### Static files not loading
- Run `python manage.py collectstatic`
- Check static files mapping in Web tab

## Success! 🎉

Your RNA Lab Navigator is now live and accessible to your entire lab without any credit card requirements!

Beta Testing URL: `https://yourusername.pythonanywhere.com`

The free tier is perfect for beta testing with your 21 lab members!