"""
Simplified and working translation service for MANAS AI Chat
"""

import json
import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class SimpleTranslationService:
    def __init__(self):
        # Language mapping for MyMemory API (format that actually works)
        self.language_mapping = {
            'hi': 'hi-IN',    # Hindi
            'bn': 'bn-IN',    # Bengali
            'te': 'te-IN',    # Telugu
            'ta': 'ta-IN',    # Tamil
            'gu': 'gu-IN',    # Gujarati
            'kn': 'kn-IN',    # Kannada
            'ml': 'ml-IN',    # Malayalam
            'mr': 'mr-IN',    # Marathi
            'pa': 'pa-IN',    # Punjabi
            'or': 'or-IN',    # Odia
            'as': 'as-IN',    # Assamese
            'ur': 'ur-PK',    # Urdu
            'es': 'es-ES',    # Spanish
            'fr': 'fr-FR',    # French
            'de': 'de-DE',    # German
            'ja': 'ja-JP',    # Japanese
            'ko': 'ko-KR',    # Korean
            'zh': 'zh-CN',    # Chinese (Simplified)
            'ar': 'ar-SA',    # Arabic
            'en': 'en-GB',    # English
        }
        
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
            'ar': 'العربية (Arabic)'
        }
        
        # UI translations in key languages
        self.ui_translations = {
            'en': {
                'hello': 'Hello',
                'goodbye': 'Goodbye', 
                'thank_you': 'Thank you',
                'please': 'Please',
                'yes': 'Yes',
                'no': 'No',
                'send': 'Send',
                'type_message': 'Type your message...',
                'new_chat': 'New Chat',
                'history': 'History',
                'delete': 'Delete',
                'translate': 'Translate',
                'language': 'Language',
                'settings': 'Settings',
                'help': 'Help',
                'loading': 'Loading...',
                'error': 'Error',
                'retry': 'Retry',
                'cancel': 'Cancel',
                'save': 'Save',
                'close': 'Close'
            },
            'hi': {
                'hello': 'नमस्ते',
                'goodbye': 'अलविदा', 
                'thank_you': 'धन्यवाद',
                'please': 'कृपया',
                'yes': 'हाँ',
                'no': 'नहीं',
                'send': 'भेजें',
                'type_message': 'अपना संदेश टाइप करें...',
                'new_chat': 'नई चैट',
                'history': 'इतिहास',
                'delete': 'हटाएं',
                'translate': 'अनुवाद करें',
                'language': 'भाषा',
                'settings': 'सेटिंग्स',
                'help': 'सहायता',
                'loading': 'लोड हो रहा है...',
                'error': 'त्रुटि',
                'retry': 'पुनः प्रयास करें',
                'cancel': 'रद्द करें',
                'save': 'सेव करें',
                'close': 'बंद करें'
            },
            'es': {
                'hello': 'Hola',
                'goodbye': 'Adiós', 
                'thank_you': 'Gracias',
                'please': 'Por favor',
                'yes': 'Sí',
                'no': 'No',
                'send': 'Enviar',
                'type_message': 'Escribe tu mensaje...',
                'new_chat': 'Nuevo Chat',
                'history': 'Historial',
                'delete': 'Eliminar',
                'translate': 'Traducir',
                'language': 'Idioma',
                'settings': 'Configuración',
                'help': 'Ayuda',
                'loading': 'Cargando...',
                'error': 'Error',
                'retry': 'Reintentar',
                'cancel': 'Cancelar',
                'save': 'Guardar',
                'close': 'Cerrar'
            }
        }

    def translate_text(self, text, target_language, source_language='en'):
        """Translate text using MyMemory API"""
        if not text or target_language == source_language:
            return text
            
        # Create cache key
        cache_key = f"translate_{hash(text)}_{source_language}_{target_language}"
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Map language codes
            source_code = self.language_mapping.get(source_language, 'en-GB')
            target_code = self.language_mapping.get(target_language, 'en-GB')
            
            # MyMemory API call
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text,
                'langpair': f"{source_code}|{target_code}"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('responseStatus') == 200:
                translated_text = data.get('responseData', {}).get('translatedText', text)
                
                # Cache for 1 hour
                cache.set(cache_key, translated_text, 3600)
                
                logger.info(f"Translation successful: {text[:30]}... -> {translated_text[:30]}...")
                return translated_text
            else:
                logger.warning(f"Translation failed: {data.get('responseDetails', 'Unknown error')}")
                return text
                
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

    def get_ui_translations(self, language='en'):
        """Get UI translations for specified language"""
        return self.ui_translations.get(language, self.ui_translations['en'])

    def get_companion_welcome_message(self, language='en', companion='arjun'):
        """Get companion welcome message in specified language"""
        welcome_messages = {
            'en': {
                'arjun': "Hello! I'm Arjun, your academic support companion. How can I help you today?",
                'priya': "Hi there! I'm Priya, your emotional support companion. I'm here to listen and support you.",
                'vikram': "Hello, I'm Vikram, your crisis support companion. I'm here for you right now. How can I help?"
            },
            'hi': {
                'arjun': "नमस्ते! मैं अर्जुन हूँ, आपका शैक्षणिक सहायता साथी। आज मैं आपकी कैसे मदद कर सकता हूँ?",
                'priya': "हैलो! मैं प्रिया हूँ, आपकी भावनात्मक सहायता साथी। मैं आपकी बात सुनने और आपका समर्थन करने के लिए यहाँ हूँ।",
                'vikram': "नमस्ते, मैं विक्रम हूँ, आपका संकट सहायता साथी। मैं अभी आपके लिए यहाँ हूँ। मैं आपकी कैसे मदद कर सकता हूँ?"
            },
            'es': {
                'arjun': "¡Hola! Soy Arjun, tu compañero de apoyo académico. ¿Cómo puedo ayudarte hoy?",
                'priya': "¡Hola! Soy Priya, tu compañera de apoyo emocional. Estoy aquí para escucharte y apoyarte.",
                'vikram': "Hola, soy Vikram, tu compañero de apoyo en crisis. Estoy aquí para ti ahora mismo. ¿Cómo puedo ayudarte?"
            }
        }
        
        # Check if we have hardcoded translations
        if language in welcome_messages and companion in welcome_messages[language]:
            return welcome_messages[language][companion]
        
        # Fall back to English and translate if needed
        english_message = welcome_messages['en'].get(companion, welcome_messages['en']['arjun'])
        
        if language == 'en':
            return english_message
            
        return self.translate_text(english_message, language, 'en')

    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.supported_languages

    def get_language_direction(self, language):
        """Get text direction for language (RTL or LTR)"""
        rtl_languages = ['ar', 'he', 'fa', 'ur']
        return 'rtl' if language in rtl_languages else 'ltr'

# Global instance
simple_translation_service = SimpleTranslationService()