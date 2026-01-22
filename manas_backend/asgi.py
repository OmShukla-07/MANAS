"""
ASGI config for MANAS Mental Health Platform Backend.

WebSocket support temporarily disabled during NLP migration.
HTTP-only mode for REST API endpoints.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manas_backend.settings")

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# Simple HTTP-only application (WebSocket support coming with n8n integration)
application = django_asgi_app
