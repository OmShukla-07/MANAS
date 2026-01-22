"""
Translation API views using Simple Translation (No API Keys Required)
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .simple_translation_service import simple_translation_service
import logging

logger = logging.getLogger(__name__)


class TranslateTextView(APIView):
    """Translate text using Google Translate API"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Translate text to target language
        
        Request body:
        {
            "text": "Text to translate",
            "target_language": "hi",
            "source_language": "en"  # optional, defaults to 'en'
        }
        """
        try:
            text = request.data.get('text')
            target_language = request.data.get('target_language', 'en')
            source_language = request.data.get('source_language', 'en')
            
            if not text:
                return Response({
                    'success': False,
                    'error': 'Text is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Translate the text
            result = simple_translation_service.translate_text(
                text=text,
                target_language=target_language,
                source_language=source_language
            )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DetectLanguageView(APIView):
    """Detect language of given text"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Detect the language of the text
        
        Request body:
        {
            "text": "Text to detect language for"
        }
        """
        try:
            text = request.data.get('text')
            
            if not text:
                return Response({
                    'success': False,
                    'error': 'Text is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Detect language
            result = simple_translation_service.detect_language(text)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupportedLanguagesView(APIView):
    """Get list of supported languages"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get all supported languages"""
        try:
            result = simple_translation_service.get_supported_languages()
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error fetching supported languages: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TranslateBatchView(APIView):
    """Translate multiple texts at once"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Translate multiple texts
        
        Request body:
        {
            "texts": ["Text 1", "Text 2", "Text 3"],
            "target_language": "hi",
            "source_language": "en"  # optional
        }
        """
        try:
            texts = request.data.get('texts', [])
            target_language = request.data.get('target_language', 'en')
            source_language = request.data.get('source_language', 'en')
            
            if not texts or not isinstance(texts, list):
                return Response({
                    'success': False,
                    'error': 'Texts array is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Translate batch
            result = simple_translation_service.translate_batch(
                texts=texts,
                target_language=target_language,
                source_language=source_language
            )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Batch translation error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
