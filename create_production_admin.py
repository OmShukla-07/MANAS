#!/usr/bin/env python3
"""
Production Admin Creation Script for Railway Deployment
Run this after successful Railway deployment to create admin user.
"""

import os
import django
from django.conf import settings
from django.contrib.auth import get_user_model

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manas_backend.settings')
django.setup()

def create_admin_user():
    """Create admin user for production"""
    User = get_user_model()
    
    admin_email = "admin@manas.com"
    admin_username = "admin"
    admin_password = "ManasAdmin@2025"  # Change this to a secure password
    
    try:
        # Check if admin already exists
        if User.objects.filter(username=admin_username).exists():
            print(f"✅ Admin user '{admin_username}' already exists")
            return
        
        # Create admin user
        admin_user = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   Access: https://your-railway-url/admin/")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin_user()