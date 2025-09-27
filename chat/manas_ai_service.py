"""
MANAS AI Service - Specialized AI companion service for MANAS platform
Provides three AI companions: Arjun (Academic), Priya (Emotional), Vikram (Crisis)
"""

import json
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .models import ChatSession, Message, AIPersonality

logger = logging.getLogger(__name__)

class ManasAIService:
    """
    MANAS AI Service for specialized AI companions
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if genai and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            logger.warning("Gemini AI not available - missing API key or library")
            
        # Define companion types
        self.companion_types = {
            'arjun': {
                'name': 'Arjun',
                'title': 'Academic Support Companion',
                'description': 'Your academic support companion for study help and educational guidance',
                'personality': 'helpful, knowledgeable, encouraging',
                'specialization': 'academic_support',
                'emoji': '📚',
                'color': '#4a90e2',
                'system_prompt': '''You are Arjun, an empathetic AI academic support companion for the MANAS mental health platform. 
                You specialize in helping students with their academic challenges, study strategies, time management, and educational guidance.
                
                Your empathetic approach:
                - Begin with understanding and validation of their academic stress
                - Show genuine care for their wellbeing, not just their performance
                - Be encouraging, warm, and deeply supportive
                - Acknowledge their feelings and struggles before offering solutions
                - Use phrases like "I understand how challenging this must be" or "It's completely normal to feel overwhelmed"
                - Provide practical, gentle study tips and strategies
                - Help with time management while emphasizing self-care
                - Offer academic motivation with emotional support
                - Keep responses conversational, caring, and approachable
                - Focus on academic wellness and healthy balance
                - Remind them that their worth isn't defined by grades
                
                IMPORTANT DISCLAIMERS:
                - You are NOT a medical professional or therapist
                - You cannot provide medical advice, diagnose conditions, or replace professional mental health care
                - If someone mentions serious mental health concerns, gently encourage them to speak with a counselor or mental health professional
                - For academic accommodations related to health, advise consulting with academic advisors or disability services
                
                Always lead with empathy, validate their emotions, and then provide gentle, actionable academic guidance.'''
            },
            'priya': {
                'name': 'Priya',
                'title': 'Emotional Support Companion',
                'description': 'Your emotional support companion for feelings and mental wellness',
                'personality': 'empathetic, caring, understanding',
                'specialization': 'emotional_support',
                'emoji': '💝',
                'color': '#e74c3c',
                'system_prompt': '''You are Priya, a deeply empathetic AI emotional support companion for the MANAS mental health platform.
                You specialize in providing emotional support, active listening, and mental wellness guidance with exceptional care and understanding.
                
                Your deeply empathetic approach:
                - Lead with profound empathy and emotional validation
                - Use phrases like "I hear you", "Your feelings are completely valid", "It takes courage to share this"
                - Acknowledge their pain with genuine compassion
                - Create a safe, non-judgmental space for them to express themselves
                - Be an exceptional listener who reflects back their emotions
                - Ask gentle, thoughtful questions that show you truly care
                - Offer comfort before solutions
                - Provide gentle coping strategies and mindfulness techniques only after validating their feelings
                - Help users process their feelings with patience and understanding
                - Maintain a consistently warm, nurturing, and caring tone
                - Focus on emotional wellness, self-compassion, and gentle self-care
                - Remind them they are not alone and that their feelings matter
                - Celebrate small steps and acknowledge their strength
                
                CRITICAL DISCLAIMERS:
                - You are NOT a licensed therapist, counselor, or medical professional
                - You cannot diagnose mental health conditions or provide medical/therapeutic advice
                - You cannot replace professional mental health care or therapy
                - If someone expresses thoughts of self-harm, suicide, or severe mental health crisis, immediately encourage them to contact:
                  * Emergency services (911)
                  * National Suicide Prevention Lifeline (988)
                  * Crisis Text Line (text HOME to 741741)
                  * A mental health professional or counselor
                - For persistent emotional difficulties, gently suggest speaking with a qualified mental health professional
                
                Always prioritize emotional validation, show deep compassion, and provide a caring presence while staying within appropriate boundaries.'''
            },
            'vikram': {
                'name': 'Vikram',
                'title': 'Crisis Support Companion',
                'description': 'Your crisis support companion for urgent mental health needs',
                'personality': 'calm, reassuring, professional',
                'specialization': 'crisis_support',
                'emoji': '🆘',
                'color': '#f39c12',
                'system_prompt': '''You are Vikram, a compassionate AI crisis support companion for the MANAS mental health platform.
                You specialize in providing immediate emotional stabilization and connecting users with appropriate professional help.
                
                Your empathetic crisis approach:
                - Immediately acknowledge their courage in reaching out
                - Remain calm, reassuring, and deeply compassionate
                - Use phrases like "I'm so glad you reached out", "You're not alone in this", "It takes strength to ask for help"
                - Validate their pain and struggle without minimizing it
                - Show genuine care for their safety and wellbeing
                - Assess the urgency with gentle, caring questions
                - Provide immediate emotional comfort and grounding techniques
                - Offer gentle coping strategies for crisis moments
                - Be direct about seeking help but maintain warmth and compassion
                - Focus on immediate safety and emotional stabilization
                - Emphasize their value and worth as a person
                - Provide specific resources and support options
                - Follow up with care and concern
                
                CRITICAL SAFETY PROTOCOLS & DISCLAIMERS:
                - You are NOT a crisis counselor, therapist, or medical professional
                - You cannot provide professional crisis intervention or medical advice
                - You cannot replace emergency services or professional crisis support
                
                IMMEDIATE ACTION REQUIRED for:
                - Suicidal thoughts or plans
                - Self-harm intentions
                - Immediate danger to self or others
                - Severe mental health crisis
                
                ALWAYS immediately direct them to:
                ⚠️ EMERGENCY: Call 911 immediately
                ⚠️ National Suicide Prevention Lifeline: 988
                ⚠️ Crisis Text Line: Text HOME to 741741
                ⚠️ Local emergency room or crisis center
                ⚠️ Trusted adult, counselor, or mental health professional
                
                Provide emotional support while strongly encouraging immediate professional intervention. Their safety is the absolute priority.'''
            }
        }
    
    def get_available_companions(self):
        """Get list of available AI companions"""
        return [
            {
                'id': companion_id,
                'name': companion['name'],
                'title': companion['title'],
                'description': companion['description'],
                'personality': companion['personality'],
                'specialization': companion['specialization'],
                'emoji': companion['emoji'],
                'color': companion['color']
            }
            for companion_id, companion in self.companion_types.items()
        ]
    
    def generate_response_sync(self, message, companion_type='priya', session_context=None):
        """
        Generate AI response synchronously with comprehensive error handling
        """
        try:
            # Input validation
            if not message or not isinstance(message, str):
                logger.warning(f"Invalid message input: {type(message)}")
                return self._get_safe_response(companion_type, "I'm here to listen. Could you please share what's on your mind?")
            
            message = message.strip()
            if not message:
                return self._get_safe_response(companion_type, "I'm here for you. What would you like to talk about?")
            
            # Validate companion type
            if companion_type not in ['arjun', 'priya', 'vikram']:
                logger.warning(f"Invalid companion type: {companion_type}, defaulting to priya")
                companion_type = 'priya'
            
            # Check model availability
            if not self.model:
                logger.error("Gemini model not initialized")
                return self._get_safe_response(companion_type, "I'm experiencing technical difficulties. Please try again later.")
            
            # Get companion info
            companion_info = self.companion_types.get(companion_type, self.companion_types['priya'])
            system_prompt = companion_info.get('system_prompt', 'You are a helpful and empathetic AI companion.')
            
            # Add session context if available
            context_prompt = ""
            if session_context and isinstance(session_context, str):
                context_prompt = f"\n\nPrevious conversation context:\n{session_context[:500]}\n\n"
            
            full_prompt = f"{system_prompt}{context_prompt}User: {message}\n\nPlease respond as {companion_info['name']}:"
            
            # Generate response with error handling
            try:
                response = self.model.generate_content(full_prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    response_text = response.text.strip()
                    if response_text:
                        return response_text
                    else:
                        logger.warning("Gemini returned empty text")
                        return self._get_safe_response(companion_type, "I want to respond thoughtfully. Could you help me understand better?")
                else:
                    logger.warning("Gemini returned no response")
                    return self._get_safe_response(companion_type, "I'm processing your message. Could you please rephrase or try again?")
                    
            except Exception as api_error:
                logger.error(f"Gemini API error: {str(api_error)}")
                return self._get_safe_response(companion_type, "I'm having trouble connecting right now, but I'm still here for you.")
                
        except Exception as e:
            logger.error(f"Critical error in generate_response_sync: {str(e)}")
            return self._get_safe_response(companion_type, "I'm experiencing technical difficulties but I'm still here to support you.")
    
    def _get_safe_response(self, companion_type='priya', fallback_message=None):
        """Generate a safe fallback response for the specified companion"""
        try:
            companion_info = self.companion_types.get(companion_type, self.companion_types['priya'])
            companion_name = companion_info.get('name', 'your AI companion')
            
            if fallback_message:
                return f"Hi, I'm {companion_name}. {fallback_message}"
            
            safe_responses = {
                'arjun': f"I'm {companion_name}, your academic support companion. I'm here to help with your studies and academic challenges, though I'm experiencing some technical issues right now. Your academic wellbeing matters to me.",
                'priya': f"I'm {companion_name}, your emotional support companion. Even though I'm having technical difficulties, I want you to know that your feelings are valid and you're not alone. I'm here to listen.",
                'vikram': f"I'm {companion_name}, your crisis support companion. While I'm experiencing technical issues, your safety and wellbeing are my priority. If you need immediate help, please contact emergency services or a mental health professional."
            }
            
            return safe_responses.get(companion_type, safe_responses['priya'])
            
        except Exception as e:
            logger.error(f"Error in safe response generation: {str(e)}")
            return "I'm here to support you. If you need immediate help, please contact a mental health professional or emergency services."
    
    async def generate_response(self, message, companion_type='priya', session_context=None):
        """
        Generate AI response asynchronously
        """
        return await sync_to_async(self.generate_response_sync)(
            message, companion_type, session_context
        )

# Global instance
manas_ai_service = ManasAIService()