FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories first
RUN mkdir -p /app/media/figures /app/static /app/logs /app/backups \
    && mkdir -p /app/backups/postgres /app/backups/weaviate /app/backups/media

# Create non-root user for security
RUN groupadd -r rnaapp && useradd -r -g rnaapp rnaapp \
    && chown -R rnaapp:rnaapp /app
USER rnaapp

# Copy entrypoint script
COPY --chown=rnaapp:rnaapp docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command - Railway sets PORT automatically
CMD ["gunicorn", "rna_backend.wsgi:application", "--bind", "0.0.0.0:$PORT", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]