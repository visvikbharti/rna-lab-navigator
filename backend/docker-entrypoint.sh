#!/bin/bash
set -e

# Set production settings if in Railway environment
if [ "$RAILWAY_ENVIRONMENT" = "production" ]; then
    export DJANGO_SETTINGS_MODULE="rna_backend.settings_production"
    echo "Using production settings"
fi

# Wait for PostgreSQL to be ready
if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_PORT" ]; then
    echo "Waiting for PostgreSQL to be ready..."
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
        sleep 0.5
    done
    echo "PostgreSQL is ready!"
fi

# Wait for Redis to be ready
if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
    echo "Waiting for Redis to be ready..."
    while ! nc -z $REDIS_HOST $REDIS_PORT; do
        sleep 0.5
    done
    echo "Redis is ready!"
fi

# Wait for Weaviate to be ready
if [ -n "$WEAVIATE_URL" ]; then
    echo "Waiting for Weaviate to be ready..."
    WEAVIATE_HOST=$(echo $WEAVIATE_URL | sed -e 's|^[^/]*//||' -e 's|[:/].*$||')
    WEAVIATE_PORT=$(echo $WEAVIATE_URL | sed -e 's|^[^:]*:||' -e 's|/.*$||')
    
    if [ -z "$WEAVIATE_PORT" ]; then
        if [[ $WEAVIATE_URL == https://* ]]; then
            WEAVIATE_PORT=443
        else
            WEAVIATE_PORT=80
        fi
    fi
    
    while ! nc -z $WEAVIATE_HOST $WEAVIATE_PORT; do
        sleep 0.5
    done
    echo "Weaviate is ready!"
fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Handle initialization tasks
if [ "$INITIALIZE_DB" = "True" ]; then
    echo "Initializing database with sample data..."
    python manage.py loaddata initial_data
fi

# Set up offline LLM if requested
if [ "$LLM_NETWORK_ISOLATION" = "True" ] && [ -n "$LOCAL_EMBEDDING_MODEL_PATH" ]; then
    echo "Setting up offline LLM models..."
    MODEL_DIR=$(dirname "$LOCAL_EMBEDDING_MODEL_PATH")
    mkdir -p $MODEL_DIR
    
    # Check if model already exists
    if [ ! -f "$LOCAL_EMBEDDING_MODEL_PATH" ]; then
        echo "Downloading embedding model..."
        python -c "
from transformers import AutoTokenizer, AutoModel
import os

model_dir = '$MODEL_DIR'
os.makedirs(model_dir, exist_ok=True)

print('Downloading sentence-transformers/all-MiniLM-L6-v2...')
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

print('Saving tokenizer and model...')
tokenizer.save_pretrained(model_dir)
model.save_pretrained(model_dir)

print('Converting model to ONNX format...')
from transformers.onnx import export
export(tokenizer_or_preprocessor=None, model=model, opset=12, output=os.path.join(model_dir, 'model.onnx'))

print('Embedding model setup complete!')
        "
    else
        echo "Embedding model already exists at $LOCAL_EMBEDDING_MODEL_PATH"
    fi
fi

# Start Celery worker and beat if requested
if [ "$START_CELERY" = "True" ]; then
    echo "Starting Celery worker and beat processes..."
    celery -A rna_backend worker -l INFO &
    celery -A rna_backend beat -l INFO &
fi

# Execute the command
exec "$@"