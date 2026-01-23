# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=manas_backend.settings
ENV PORT=8000
ENV DISABLE_HUGGINGFACE=false

# Run migrations and start server
CMD python manage.py migrate && \
    python manage.py createcachetable && \
    gunicorn manas_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 300
