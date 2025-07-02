#!/bin/bash
set -e

echo "Starting Railway deployment..."

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations --no-input || true
python manage.py migrate --no-input

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Create superuser if it doesn't exist
echo "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@rnalabnavigator.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Start the server
echo "Starting Gunicorn..."
exec gunicorn rna_backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info