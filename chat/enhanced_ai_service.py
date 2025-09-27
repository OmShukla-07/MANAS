"""
Enhanced MANAS AI Service with Multiple AI Providers
Supports both Google Gemini and OpenAI ChatGPT
"""

import json
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async

# Import AI services
try:
    from .manas_ai_service import manas_ai_service as gemini_service
except ImportError:
    gemini_service = None

try:
    from .openai_service import openai_service
except ImportError:
    openai_service = None

from .models import ChatSession, Message, AIPersonality

logger = logging.getLogger(__name__)

class EnhancedManasAIService:
    """
    Enhanced MANAS AI Service supporting multiple AI providers
    """
    
    def __init__(self):
        self.providers = {}
        
        # Register available providers
        if gemini_service and hasattr(gemini_service, 'model') and gemini_service.model:
            self.providers['gemini'] = {
                'service': gemini_service,
                'name': 'Google Gemini',
                'model': 'gemini-2.5-flash',
                'available': True
            }
        
        if openai_service and hasattr(openai_service, 'client') and openai_service.client:
            self.providers['openai'] = {
                'service': openai_service,
                'name': 'OpenAI ChatGPT',
                'model': 'gpt-3.5-turbo',
                'available': True
            }
        
        # Set default provider
        self.default_provider = self._get_default_provider()
        
        logger.info(f"Enhanced MANAS AI initialized with providers: {list(self.providers.keys())}")
        logger.info(f"Default provider: {self.default_provider}")
    
    def _get_default_provider(self):
        """Determine the best available provider"""
        if 'gemini' in self.providers:
            return 'gemini'
        elif 'openai' in self.providers:
            return 'openai'
        else:
            return None
    
    def get_available_providers(self):
        """Get list of available AI providers"""
        return [
            {
                'id': provider_id,
                'name': provider_info['name'],
                'model': provider_info['model'],
                'available': provider_info['available']
            }
            for provider_id, provider_info in self.providers.items()
        ]
    
    def get_available_companions(self, provider=None):
        """Get list of available AI companions"""
        provider = provider or self.default_provider
        if provider and provider in self.providers:
            service = self.providers[provider]['service']
            companions = service.get_available_companions()
            # Add provider info to each companion
            for companion in companions:
                companion['provider'] = provider
                companion['provider_name'] = self.providers[provider]['name']
            return companions
        return []
    
    def generate_response_sync(self, message, companion_type='priya', session_context=None, provider=None):
        """
        Generate AI response synchronously with comprehensive error handling and fallback support
        """
        try:
            # Input validation
            if not message or not isinstance(message, str):
                logger.warning(f"Invalid message input: {type(message)}")
                return self._get_safe_fallback_response(companion_type, "I'm here to listen. Could you please share what's on your mind?")
            
            message = message.strip()
            if not message:
                return self._get_safe_fallback_response(companion_type, "I'm here for you. What would you like to talk about?")
            
            # Validate companion type
            if companion_type not in ['arjun', 'priya', 'vikram']:
                logger.warning(f"Invalid companion type: {companion_type}, defaulting to priya")
                companion_type = 'priya'
            
            provider = provider or self.default_provider
            
            # Try primary provider
            if provider and provider in self.providers:
                try:
                    service = self.providers[provider]['service']
                    response = service.generate_response_sync(message, companion_type, session_context)
                    
                    # Validate response
                    if response and (isinstance(response, str) or isinstance(response, dict)):
                        logger.info(f"Response generated using {provider}")
                        return {
                            'content': response,
                            'provider': provider,
                            'provider_name': self.providers[provider]['name'],
                            'model': self.providers[provider]['model']
                        }
                    else:
                        logger.warning(f"Provider {provider} returned invalid response")
                        
                except Exception as e:
                    logger.error(f"Primary provider {provider} failed: {e}")
            
            # Try fallback providers
            for fallback_provider, provider_info in self.providers.items():
                if fallback_provider != provider:
                    try:
                        service = provider_info['service']
                        response = service.generate_response_sync(message, companion_type, session_context)
                        
                        # Validate response
                        if response and (isinstance(response, str) or isinstance(response, dict)):
                            logger.info(f"Response generated using fallback provider {fallback_provider}")
                            return {
                                'content': response,
                                'provider': fallback_provider,
                                'provider_name': provider_info['name'],
                                'model': provider_info['model']
                            }
                        else:
                            logger.warning(f"Fallback provider {fallback_provider} returned invalid response")
                            
                    except Exception as e:
                        logger.error(f"Fallback provider {fallback_provider} failed: {e}")
            
            # All providers failed - return safe fallback
            logger.error("All AI providers failed, using safe fallback response")
            return self._get_safe_fallback_response(companion_type)
            
        except Exception as e:
            logger.error(f"Critical error in generate_response_sync: {str(e)}")
            return self._get_safe_fallback_response(companion_type, "I'm experiencing technical difficulties but I'm still here to support you.")
    
    def _get_safe_fallback_response(self, companion_type='priya', custom_message=None):
        """Get safe fallback response when all AI providers fail"""
        try:
            # Validate companion type
            if companion_type not in ['arjun', 'priya', 'vikram']:
                companion_type = 'priya'
            
            companion_names = {'arjun': 'Arjun', 'priya': 'Priya', 'vikram': 'Vikram'}
            companion_name = companion_names.get(companion_type, 'your companion')
            
            if custom_message:
                content = f"Hi, I'm {companion_name}. {custom_message}"
            else:
                fallback_messages = {
                    'arjun': f"Hi, I'm {companion_name}, your academic support companion. I'm experiencing some technical difficulties, but I want you to know that your academic challenges are valid. Please consider speaking with a counselor or academic advisor for immediate guidance. I'll be back to full functionality soon.",
                    'priya': f"Hello, I'm {companion_name}, your emotional support companion. While I'm having technical issues, I want you to know that your feelings matter and you're not alone. If you're in distress, please reach out to a counselor or mental health professional. I care about your wellbeing.",
                    'vikram': f"I'm {companion_name}, your crisis support companion. While experiencing technical difficulties, your safety is my priority. If you're in immediate danger, call 911. For mental health crisis: 988 (Suicide & Crisis Lifeline) or text HOME to 741741. Professional help is available."
                }
                content = fallback_messages.get(companion_type, fallback_messages['priya'])
            
            return {
                'content': content,
                'provider': 'fallback',
                'provider_name': 'MANAS Safe Fallback',
                'model': 'fallback-system'
            }
            
        except Exception as e:
            logger.error(f"Error in safe fallback response: {str(e)}")
            return {
                'content': "I'm here to support you. If you need immediate help, please contact a mental health professional or emergency services.",
                'provider': 'emergency',
                'provider_name': 'Emergency Fallback', 
                'model': 'emergency-system'
            }
    
    async def generate_response(self, message, companion_type='priya', session_context=None, provider=None):
        """
        Generate AI response asynchronously
        """
        return await sync_to_async(self.generate_response_sync)(
            message, companion_type, session_context, provider
        )
    
    def get_provider_status(self):
        """Get status of all providers"""
        status = {}
        for provider_id, provider_info in self.providers.items():
            try:
                service = provider_info['service']
                # Test with a simple message
                test_response = service.generate_response_sync("Hello", "priya")
                status[provider_id] = {
                    'available': True,
                    'name': provider_info['name'],
                    'model': provider_info['model'],
                    'test_response_length': len(test_response) if isinstance(test_response, str) else len(str(test_response))
                }
            except Exception as e:
                status[provider_id] = {
                    'available': False,
                    'name': provider_info['name'],
                    'model': provider_info['model'],
                    'error': str(e)
                }
        return status

# Global enhanced service instance
enhanced_manas_ai_service = EnhancedManasAIService()