#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting MANAS build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🗃️ Running database migrations..."
python manage.py migrate --noinput

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🔧 Creating cache table..."
python manage.py createcachetable || echo "Cache table already exists"

echo "✅ Build completed successfully!"