#!/usr/bin/env python3
"""
Create cache table migration for Railway deployment.
This creates the cache_table needed for database caching.
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manas_backend.settings')
    django.setup()
    
    print("🔧 Creating cache table for Railway deployment...")
    
    try:
        # Create cache table
        execute_from_command_line(['manage.py', 'createcachetable'])
        print("✅ Cache table created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating cache table: {e}")
        sys.exit(1)