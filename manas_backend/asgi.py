"""
ASGI config for MANAS Mental Health Platform Backend.

Supports both HTTP and WebSocket connections for real-time chat functionality.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manas_backend.settings")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import chat routing and middleware after Django is initialized
from chat.routing import websocket_urlpatterns
from chat.middleware import WebSocketAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        WebSocketAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
