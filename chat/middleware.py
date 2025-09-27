"""
Custom middleware for WebSocket JWT authentication.
Handles JWT token validation for WebSocket connections.
"""

import jwt
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.conf import settings
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

User = get_user_model()


@database_sync_to_async
def get_user_by_id(user_id):
    """Get user by ID from database"""
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    
    Expects token to be passed as query parameter: ?token=<jwt_token>
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query parameters
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if token:
            try:
                # Validate JWT token
                validated_token = UntypedToken(token)
                user_id = validated_token['user_id']
                
                # Get user from database
                scope['user'] = await get_user_by_id(user_id)
                
            except (InvalidToken, TokenError, KeyError):
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


class WebSocketAuthMiddleware:
    """
    Middleware stack for WebSocket authentication.
    Combines JWT authentication with Channels auth middleware.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Apply JWT authentication
        jwt_middleware = JWTAuthMiddleware(self.app)
        return await jwt_middleware(scope, receive, send)


# Middleware stack for WebSocket authentication
def WebSocketAuthMiddlewareStack(inner):
    """Create WebSocket authentication middleware stack"""
    return WebSocketAuthMiddleware(inner)