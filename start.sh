#!/bin/bash

# Hugging Face Space startup script

echo "🚀 Starting MANAS Mental Health Platform..."

# Run database migrations
python manage.py migrate --noinput

# Create cache table
python manage.py createcachetable

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn server
exec gunicorn manas_backend.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 4 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
