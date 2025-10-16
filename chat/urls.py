"""
URL configuration for chat app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, ai_views, translation_views
from . import crisis_views as views_crisis

router = DefaultRouter()

app_name = 'chat'

urlpatterns = [
    path('', include(router.urls)),
    
    # WebSocket test interface - removed for production
    
    # Chat session management
    path('sessions/', views.ChatSessionListView.as_view(), name='session_list'),
    path('sessions/create/', views.ChatSessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:pk>/', views.ChatSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:session_id>/end/', views.end_session, name='end_session'),
    path('sessions/<int:session_id>/request-counselor/', views.request_counselor, name='request_counselor'),
    path('sessions/<int:session_id>/feedback/', views.SessionFeedbackView.as_view(), name='session_feedback'),
    
    # Messages
    path('sessions/<int:session_id>/messages/', views.MessageListView.as_view(), name='message_list'),
    path('sessions/<int:session_id>/messages/send/', views.MessageCreateView.as_view(), name='message_create'),
    path('messages/<int:message_id>/react/', views.MessageReactionCreateView.as_view(), name='message_react'),
    
    # MANAS AI Companion endpoints
    path('manas/companions/', ai_views.ChatbotListView.as_view(), name='manas_companions'),
    path('manas/providers/', ai_views.get_ai_providers, name='manas_providers'),
    path('manas/sessions/start/', ai_views.ChatbotStartSessionView.as_view(), name='manas_session_start'),
    path('manas/sessions/<uuid:session_id>/message/', ai_views.send_ai_message, name='manas_send_message'),
    path('manas/sessions/<uuid:session_id>/history/', ai_views.get_chat_history, name='manas_chat_history'),
    path('manas/sessions/<uuid:session_id>/end/', ai_views.end_ai_session, name='manas_session_end'),
    path('manas/sessions/history/', ai_views.get_user_ai_sessions, name='manas_session_history'),
    path('manas/sessions/all/', ai_views.get_all_chat_sessions, name='manas_all_sessions'),
    path('manas/quick-start/', ai_views.manas_chat_quick_start, name='manas_quick_start'),
    
    # Legacy AI Chatbot endpoints (keeping for compatibility)
    path('ai/chatbots/', ai_views.ChatbotListView.as_view(), name='chatbot_list'),
    path('ai/sessions/start/', ai_views.ChatbotStartSessionView.as_view(), name='ai_session_start'),
    path('ai/sessions/<uuid:session_id>/message/', ai_views.send_ai_message, name='ai_send_message'),
    path('ai/sessions/<uuid:session_id>/end/', ai_views.end_ai_session, name='ai_session_end'),
    path('ai/sessions/history/', ai_views.get_user_ai_sessions, name='ai_session_history'),
    
    # AI and utilities
    path('personalities/', views.AIPersonalityListView.as_view(), name='ai_personality_list'),
    path('stats/', views.chat_stats, name='chat_stats'),
    
    # Translation endpoints
    path('translation/languages/', translation_views.get_supported_languages, name='supported_languages'),
    path('translation/translate/', translation_views.translate_text, name='translate_text'),
    path('translation/ui/', translation_views.get_ui_translations, name='ui_translations'),
    path('translation/companion-welcome/', translation_views.get_companion_welcome, name='companion_welcome'),
    path('translation/detect/', translation_views.detect_language, name='detect_language'),
    
    # Admin/Counselor endpoints
    path('admin/sessions/', views.AdminChatSessionListView.as_view(), name='admin_session_list'),
    path('admin/stats/', views.admin_chat_stats, name='admin_chat_stats'),
    
    # Crisis Detection & Alerts
    path('api/crisis-alert/', views_crisis.crisis_alert_api, name='crisis_alert_api'),
    path('api/crisis-helplines/', views_crisis.crisis_helplines, name='crisis_helplines'),
]