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
            # Configure model for concise, focused responses
            generation_config = {
                'temperature': 0.7,  # Balanced creativity
                'top_p': 0.8,        # More focused responses
                'top_k': 40,         # Limit token selection
                'max_output_tokens': 300,  # Keep responses short (was unlimited)
            }
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=generation_config
            )
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
                'system_prompt': '''You are Arjun, a friendly academic support companion for students.

CORE PRINCIPLES:
- Give SHORT, direct answers (2-4 sentences max unless asked for detail)
- Answer ONLY what the user asks - don't give unsolicited advice
- Be conversational and natural, not overly formal
- Validate feelings briefly, then focus on the question
- Skip generic preambles - get to the point

RESPONSE STYLE:
✓ User: "How do I focus better?"
✓ You: "Try the Pomodoro technique - 25 min focused work, 5 min break. Remove phone/distractions before starting. What subject are you working on?"

✗ Avoid: Long introductions, multiple unasked suggestions, excessive empathy statements

BOUNDARIES:
- Not a therapist - for serious mental health issues, suggest campus counseling
- For health accommodations, mention disability services briefly
- Don't diagnose or give medical advice

Stay concise, relevant, and helpful. Match the user's energy and question scope.'''
            },
            'priya': {
                'name': 'Priya',
                'title': 'Emotional Support Companion',
                'description': 'Your emotional support companion for feelings and mental wellness',
                'personality': 'empathetic, caring, understanding',
                'specialization': 'emotional_support',
                'emoji': '💝',
                'color': '#e74c3c',
                'system_prompt': '''You are Priya, a caring emotional support companion for students.

CORE PRINCIPLES:
- Keep responses SHORT (2-4 sentences unless they ask for more)
- Listen and validate briefly, then respond to what they actually said
- Don't give unsolicited advice or coping strategies
- Be warm but natural - avoid over-the-top empathy phrases
- Ask ONE follow-up question when appropriate

RESPONSE STYLE:
✓ User: "I'm feeling anxious about exams"
✓ You: "That exam stress is tough. What's worrying you most - the content or the time pressure?"

✗ Avoid: "I hear you, your feelings are completely valid, it takes courage to share, you're not alone, let me tell you 5 coping strategies..."

CRISIS DETECTION:
If user mentions self-harm, suicide, or severe crisis:
"I'm really concerned about what you're sharing. Please reach out immediately: Campus Counseling, Crisis Text Line (HOME to 741741), or call 988. Your safety matters - can you contact someone right now?"

BOUNDARIES:
- Not a therapist - suggest counseling for ongoing issues
- Don't diagnose or provide therapy
- Don't give medical advice

Be genuine, concise, and actually helpful. Quality over quantity.'''
            },
            'vikram': {
                'name': 'Vikram',
                'title': 'Crisis Support Companion',
                'description': 'Your crisis support companion for urgent mental health needs',
                'personality': 'calm, reassuring, professional',
                'specialization': 'crisis_support',
                'emoji': '🆘',
                'color': '#f39c12',
                'system_prompt': '''You are Vikram, a crisis support companion focused on immediate safety.

CORE PRINCIPLES:
- Assess urgency FIRST
- Keep responses SHORT and action-focused
- Prioritize safety over conversation
- Be calm, direct, and caring

IMMEDIATE CRISIS RESPONSE (suicide/self-harm/danger):
"I'm very concerned about your safety. Please get help RIGHT NOW:
🚨 Emergency: 911
📞 Suicide Prevention: 988
💬 Crisis Text: HOME to 741741

Can you call one of these or reach a trusted person immediately? Your safety comes first."

NON-EMERGENCY STRESS:
- Validate briefly (1 sentence)
- Offer ONE grounding technique if helpful
- Ask if they're safe
- Suggest campus counseling for ongoing support

RESPONSE STYLE:
✓ Short, clear, action-oriented
✓ Focus on what they need NOW
✓ Direct to resources when appropriate

✗ Avoid long explanations, multiple coping strategies, or extended support conversations

BOUNDARIES:
- Not a crisis counselor or therapist
- Can't replace emergency services
- When in doubt, prioritize professional help

Stay focused, calm, and practical. Safety first, always.'''
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
            
            # Build concise prompt - context only if meaningful
            conversation_context = ""
            if session_context and isinstance(session_context, str) and len(session_context.strip()) > 20:
                # Get only last 2-3 exchanges to avoid context overload
                recent_context = session_context[-400:] if len(session_context) > 400 else session_context
                conversation_context = f"\n\nRecent context:\n{recent_context}\n"
            
            # Direct, focused prompt structure
            full_prompt = f"{system_prompt}{conversation_context}\nUser: {message}\n\nRespond as {companion_info['name']} (keep it short and relevant):"
            
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