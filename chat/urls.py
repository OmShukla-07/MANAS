"""
URL configuration for chat app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import translation_views

router = DefaultRouter()

app_name = 'chat'

urlpatterns = [
    # API endpoints for NLP chatbot
    path('api/companions/', views.ChatbotCompanionsView.as_view(), name='chatbot_companions'),
    path('api/session/start/', views.ChatSessionStartView.as_view(), name='session_start'),
    path('api/message/send/', views.ChatMessageSendView.as_view(), name='message_send'),
    path('api/sessions/', views.ChatSessionListView.as_view(), name='session_list'),
    path('api/session/<int:session_id>/', views.ChatSessionDetailView.as_view(), name='session_detail'),
    path('api/session/<int:session_id>/end/', views.ChatSessionEndView.as_view(), name='session_end'),
    
    # Translation API endpoints
    path('api/translate/', translation_views.TranslateTextView.as_view(), name='translate_text'),
    path('api/translate/detect/', translation_views.DetectLanguageView.as_view(), name='detect_language'),
    path('api/translate/languages/', translation_views.SupportedLanguagesView.as_view(), name='supported_languages'),
    path('api/translate/batch/', translation_views.TranslateBatchView.as_view(), name='translate_batch'),
    
    # Router URLs
    path('', include(router.urls)),
]
