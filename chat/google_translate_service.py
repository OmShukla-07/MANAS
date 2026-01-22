"""
Google Translate API integration for MANAS AI Chat
Provides translation services using Google Cloud Translation API
"""

import logging
from google.cloud.translate_v2 import Client
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class GoogleTranslateService:
    def __init__(self):
        """Initialize Google Translate client"""
        self.client = None
        self.supported_languages = {
            'en': 'English',
            'hi': 'हिंदी (Hindi)',
            'bn': 'বাংলা (Bengali)', 
            'te': 'తెలుగు (Telugu)',
            'mr': 'मराठी (Marathi)',
            'ta': 'தமிழ் (Tamil)',
            'gu': 'ગુજરાતી (Gujarati)',
            'kn': 'ಕನ್ನಡ (Kannada)',
            'ml': 'മലയാളം (Malayalam)',
            'pa': 'ਪੰਜਾਬੀ (Punjabi)',
            'or': 'ଓଡ଼ିଆ (Odia)',
            'as': 'অসমীয়া (Assamese)',
            'ur': 'اردو (Urdu)',
            'es': 'Español (Spanish)',
            'fr': 'Français (French)',
            'de': 'Deutsch (German)',
            'ja': '日本語 (Japanese)',
            'ko': '한국어 (Korean)',
            'zh': '中文 (Chinese)',
            'ar': 'العربية (Arabic)',
            'pt': 'Português (Portuguese)',
            'ru': 'Русский (Russian)',
            'it': 'Italiano (Italian)',
            'nl': 'Nederlands (Dutch)',
            'tr': 'Türkçe (Turkish)',
            'vi': 'Tiếng Việt (Vietnamese)',
            'th': 'ไทย (Thai)',
            'id': 'Bahasa Indonesia',
            'ms': 'Bahasa Melayu',
            'fil': 'Filipino',
            'ne': 'नेपाली (Nepali)',
            'si': 'සිංහල (Sinhala)'
        }
        
        try:
            # Initialize Google Translate client
            self.client = Client()
            logger.info("Google Translate API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Translate client: {e}")
            logger.warning("Translation services will not be available")

    def translate_text(self, text, target_language, source_language='en'):
        """
        Translate text using Google Translate API
        
        Args:
            text (str): Text to translate
            target_language (str): Target language code
            source_language (str): Source language code (default: 'en')
            
        Returns:
            str: Translated text or original text if translation fails
        """
        if not text or not text.strip():
            return text
            
        if target_language == source_language:
            return text
            
        # Check if client is initialized
        if not self.client:
            logger.warning("Google Translate client not initialized, returning original text")
            return text
        
        # Create cache key
        cache_key = f"gtranslate_{hash(text)}_{source_language}_{target_language}"
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Translation cache hit for: {text[:30]}...")
            return cached_result
        
        try:
            # Perform translation
            result = self.client.translate(
                text,
                target_language=target_language,
                source_language=source_language
            )
            
            translated_text = result['translatedText']
            
            # Cache for 1 hour
            cache.set(cache_key, translated_text, 3600)
            
            logger.info(f"Translation successful: {text[:30]}... -> {translated_text[:30]}...")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

    def detect_language(self, text):
        """
        Detect the language of the given text
        
        Args:
            text (str): Text to detect language for
            
        Returns:
            dict: Dictionary with 'language' code and 'confidence' score
        """
        if not self.client or not text:
            return {'language': 'en', 'confidence': 0.0}
        
        try:
            result = self.client.detect_language(text)
            return {
                'language': result['language'],
                'confidence': result['confidence']
            }
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {'language': 'en', 'confidence': 0.0}

    def translate_batch(self, texts, target_language, source_language='en'):
        """
        Translate multiple texts at once
        
        Args:
            texts (list): List of texts to translate
            target_language (str): Target language code
            source_language (str): Source language code
            
        Returns:
            list: List of translated texts
        """
        if not self.client or not texts:
            return texts
        
        if target_language == source_language:
            return texts
        
        try:
            results = self.client.translate(
                texts,
                target_language=target_language,
                source_language=source_language
            )
            
            return [result['translatedText'] for result in results]
            
        except Exception as e:
            logger.error(f"Batch translation error: {e}")
            return texts

    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.supported_languages

    def get_language_direction(self, language):
        """Get text direction for language (RTL or LTR)"""
        rtl_languages = ['ar', 'he', 'fa', 'ur']
        return 'rtl' if language in rtl_languages else 'ltr'

    def is_available(self):
        """Check if Google Translate service is available"""
        return self.client is not None

# Global instance
google_translate_service = GoogleTranslateService()
