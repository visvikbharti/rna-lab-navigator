FROM python:3.11-slim

WORKDIR /app

# Install all dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=rna_backend.settings_production

# Change to backend directory
WORKDIR /app/backend

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Starting RNA Lab Navigator..."\n\
echo "DATABASE_URL: ${DATABASE_URL:0:20}..."\n\
echo "Running migrations with proper order..."\n\
# First run contenttypes and auth migrations\n\
python manage.py migrate contenttypes --noinput || echo "contenttypes migration failed"\n\
python manage.py migrate auth --noinput || echo "auth migration failed"\n\
# Then run our custom user model migration\n\
python manage.py makemigrations api_auth --noinput || echo "makemigrations failed"\n\
python manage.py migrate api_auth --noinput || echo "api_auth migration failed"\n\
# Finally run all remaining migrations\n\
python manage.py migrate --noinput || echo "Other migrations failed"\n\
echo "Creating superuser..."\n\
python manage.py shell -c "\n\
from django.contrib.auth import get_user_model;\n\
User = get_user_model();\n\
if User.objects.count() == 0:\n\
    User.objects.create_superuser(\"admin\", \"admin@rnalab.com\", \"admin123\");\n\
    print(\"Superuser created successfully\");\n\
else:\n\
    print(\"Users already exist\");\n\
" || echo "Superuser creation failed"\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput || echo "Collectstatic failed"\n\
echo "Starting Gunicorn..."\n\
exec gunicorn rna_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000}' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint
CMD ["/entrypoint.sh"]