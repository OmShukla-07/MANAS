"""
Translation views for MANAS AI Chat
Provides REST API endpoints for translation services
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

from .simple_translation_service import simple_translation_service

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access
def get_supported_languages(request):
    """Get list of supported languages"""
    try:
        languages = simple_translation_service.get_supported_languages()
        return Response({
            'success': True,
            'languages': languages
        })
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def translate_text(request):
    """Translate text to target language"""
    try:
        data = request.data
        text = data.get('text', '')
        target_language = data.get('target_language', 'en')
        source_language = data.get('source_language', 'auto')
        
        if not text:
            return Response({
                'success': False,
                'error': 'Text is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        translated_text = simple_translation_service.translate_text(
            text, target_language, source_language
        )
        
        return Response({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language
        })
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def get_ui_translations(request):
    """Get UI text translations for specified language"""
    try:
        data = request.data
        language = data.get('language', 'en')
        keys = data.get('keys', [])
        
        if not keys:
            # Return all UI translations if no specific keys requested
            keys = [
                'app_title', 'academic_support', 'emotional_support', 'crisis_support',
                'chat_history', 'new_chat', 'type_message', 'send', 'no_sessions',
                'start_conversation', 'delete_confirm', 'cannot_undo', 'messages',
                'just_now', 'hours_ago', 'days_ago', 'you', 'language',
                'select_language', 'translate_messages', 'original_language',
                'connection_error'
            ]
        
        translations = {}
        for key in keys:
            translations[key] = simple_translation_service.get_ui_translations(language).get(key, key)
        
        return Response({
            'success': True,
            'language': language,
            'translations': translations
        })
        
    except Exception as e:
        logger.error(f"UI translation error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def get_companion_welcome(request):
    """Get translated companion welcome message"""
    try:
        data = request.data
        companion = data.get('companion', 'arjun')
        language = data.get('language', 'en')
        
        welcome_message = simple_translation_service.get_companion_welcome_message(
            language, companion
        )
        
        return Response({
            'success': True,
            'companion': companion,
            'language': language,
            'welcome_message': welcome_message
        })
        
    except Exception as e:
        logger.error(f"Companion welcome translation error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def detect_language(request):
    """Detect language of given text"""
    try:
        data = request.data
        text = data.get('text', '')
        
        if not text:
            return Response({
                'success': False,
                'error': 'Text is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # For now, default to English (language detection would require additional API)
        detected_language = 'en'
        language_name = simple_translation_service.get_supported_languages().get(
            detected_language, 'Unknown'
        )
        
        return Response({
            'success': True,
            'text': text,
            'detected_language': detected_language,
            'language_name': language_name
        })
        
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)