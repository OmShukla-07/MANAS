#!/usr/bin/env python
"""
WSGI config for production deployment
"""
import os
from django.core.wsgi import application
from django.conf import settings

# This is for production deployment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manas_backend.settings')