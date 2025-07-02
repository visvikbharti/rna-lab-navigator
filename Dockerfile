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
echo "Running migrations..."\n\
python manage.py migrate --noinput || echo "Migration failed, continuing..."\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput || echo "Collectstatic failed, continuing..."\n\
echo "Starting Gunicorn..."\n\
exec gunicorn rna_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000}' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint
CMD ["/entrypoint.sh"]