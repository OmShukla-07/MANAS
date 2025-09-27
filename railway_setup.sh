#!/bin/bash
# Railway Deployment Script
# This script runs after code deployment to set up the database properly

echo "🚀 Railway Deployment: Setting up MANAS Mental Health Platform..."

# Apply database migrations
echo "📦 Applying database migrations..."
python manage.py migrate --noinput

# Create cache table for database caching
echo "🗄️ Creating cache table..."
python manage.py createcachetable

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "👤 Checking for admin user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@manas.com', 'ManasAdmin@2025')
    print('✅ Admin user created: admin / ManasAdmin@2025')
else:
    print('✅ Admin user already exists')
"

echo "🎉 Railway deployment setup completed!"
echo "🌐 Your MANAS platform should now be accessible!"