"""
WebSocket URL routing for chat functionality.
Handles real-time chat sessions, notifications, and crisis alerts.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat session WebSocket - for real-time messaging
    re_path(r'ws/chat/(?P<session_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    
    # User notifications WebSocket - for real-time notifications
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', consumers.NotificationConsumer.as_asgi()),
    
    # Crisis alerts WebSocket - for emergency notifications to counselors
    re_path(r'ws/crisis/(?P<user_id>\w+)/$', consumers.CrisisConsumer.as_asgi()),
    
    # Admin monitoring WebSocket - for real-time admin dashboard
    re_path(r'ws/admin/monitoring/$', consumers.AdminMonitoringConsumer.as_asgi()),
]