"""
Simple Translation Service - No API Keys Required
Uses free MyMemory Translation API
"""

import logging
import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

class SimpleTranslationService:
    """Free translation service using MyMemory API - No setup required"""
    
    def __init__(self):
        self.base_url = "https://api.mymemory.translated.net/get"
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
        }
    
    def translate_text(self, text, target_language, source_language='en'):
        """
        Translate text using MyMemory free API
        
        Args:
            text (str): Text to translate
            target_language (str): Target language code (e.g., 'hi', 'es')
            source_language (str): Source language code (default: 'en')
            
        Returns:
            dict: Translation result with translated text
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': 'Empty text provided'
            }
        
        # Check cache first
        cache_key = f"translation_{source_language}_{target_language}_{text[:50]}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Translation cache hit for: {text[:30]}...")
            return cached_result
        
        try:
            # Make API request
            params = {
                'q': text,
                'langpair': f'{source_language}|{target_language}'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('responseStatus') == 200:
                translated_text = data['responseData']['translatedText']
                
                result = {
                    'success': True,
                    'original_text': text,
                    'translated_text': translated_text,
                    'source_language': source_language,
                    'target_language': target_language
                }
                
                # Cache for 1 hour
                cache.set(cache_key, result, 3600)
                
                logger.info(f"Translation successful: {text[:30]}... -> {translated_text[:30]}...")
                return result
            else:
                return {
                    'success': False,
                    'error': 'Translation failed',
                    'original_text': text
                }
                
        except requests.RequestException as e:
            logger.error(f"Translation API request failed: {e}")
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
                'original_text': text
            }
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_text': text
            }
    
    def detect_language(self, text):
        """
        Basic language detection (limited functionality with free API)
        
        Args:
            text (str): Text to detect language
            
        Returns:
            dict: Detected language info
        """
        # Simple heuristic detection based on character sets
        if any('\u0900' <= char <= '\u097F' for char in text):
            return {'success': True, 'detected_language': 'hi', 'confidence': 0.8}
        elif any('\u0980' <= char <= '\u09FF' for char in text):
            return {'success': True, 'detected_language': 'bn', 'confidence': 0.8}
        elif any('\u0C00' <= char <= '\u0C7F' for char in text):
            return {'success': True, 'detected_language': 'te', 'confidence': 0.8}
        elif any('\u0B80' <= char <= '\u0BFF' for char in text):
            return {'success': True, 'detected_language': 'ta', 'confidence': 0.8}
        elif any('\u0A80' <= char <= '\u0AFF' for char in text):
            return {'success': True, 'detected_language': 'gu', 'confidence': 0.8}
        elif any('\u0600' <= char <= '\u06FF' for char in text):
            return {'success': True, 'detected_language': 'ar', 'confidence': 0.8}
        elif any('\u4E00' <= char <= '\u9FFF' for char in text):
            return {'success': True, 'detected_language': 'zh', 'confidence': 0.8}
        else:
            return {'success': True, 'detected_language': 'en', 'confidence': 0.6}
    
    def translate_batch(self, texts, target_language, source_language='en'):
        """
        Translate multiple texts
        
        Args:
            texts (list): List of texts to translate
            target_language (str): Target language code
            source_language (str): Source language code
            
        Returns:
            dict: Batch translation results
        """
        translated_texts = []
        
        for text in texts:
            result = self.translate_text(text, target_language, source_language)
            if result.get('success'):
                translated_texts.append(result['translated_text'])
            else:
                translated_texts.append(text)  # Keep original if translation fails
        
        return {
            'success': True,
            'original_texts': texts,
            'translated_texts': translated_texts,
            'source_language': source_language,
            'target_language': target_language,
            'count': len(translated_texts)
        }
    
    def get_supported_languages(self):
        """Return list of supported languages"""
        return {
            'success': True,
            'languages': self.supported_languages,
            'count': len(self.supported_languages)
        }


# Create singleton instance
simple_translation_service = SimpleTranslationService()
