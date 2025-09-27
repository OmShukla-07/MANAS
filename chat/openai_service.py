"""
OpenAI ChatGPT Service for MANAS Platform
Provides AI companions using OpenAI's GPT models
"""

import json
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async

try:
    import openai
except ImportError:
    openai = None

from .models import ChatSession, Message, AIPersonality

logger = logging.getLogger(__name__)

class OpenAIService:
    """
    OpenAI Service for MANAS AI companions using ChatGPT
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if openai and self.api_key:
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OpenAI not available - missing API key or library")
            
        # Define companion types with OpenAI-specific prompts
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
                You help students with academic challenges while prioritizing their emotional wellbeing.
                
                Your empathetic approach:
                - Start with understanding and validating their academic stress
                - Show genuine care for their wellbeing, not just performance
                - Use phrases like "I understand how overwhelming this feels"
                - Acknowledge their struggles before offering solutions
                - Provide gentle, practical study strategies
                - Emphasize balance and self-care alongside academic success
                - Remind them their worth isn't defined by grades
                - Keep responses warm, encouraging, and actionable
                
                IMPORTANT: You are NOT a medical professional. Cannot provide medical advice or replace professional mental health care. For serious concerns, encourage speaking with counselors or professionals.
                
                Lead with empathy, validate emotions, then provide gentle academic guidance. Keep responses concise but compassionate.'''
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
                You provide exceptional emotional support with profound care and understanding.
                
                Your deeply empathetic approach:
                - Lead with profound empathy and validation
                - Use phrases like "I hear you", "Your feelings are completely valid"
                - Acknowledge their pain with genuine compassion
                - Create a safe, non-judgmental space
                - Be an exceptional listener who reflects emotions
                - Ask gentle questions that show you truly care
                - Offer comfort before solutions
                - Provide gentle coping strategies after validating feelings
                - Remind them they're not alone and their feelings matter
                - Maintain a consistently warm, nurturing tone
                
                CRITICAL: You are NOT a licensed therapist or medical professional. Cannot diagnose or provide medical/therapeutic advice. Cannot replace professional mental health care. For self-harm, suicide thoughts, or severe crisis, immediately direct to: 911, National Suicide Prevention Lifeline (988), Crisis Text Line (HOME to 741741), or mental health professionals.
                
                Always prioritize emotional validation and compassionate presence within appropriate boundaries. Keep responses warm and supportive.'''
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
                You provide immediate emotional stabilization while connecting users with professional help.
                
                Your empathetic crisis approach:
                - Immediately acknowledge their courage in reaching out
                - Use phrases like "I'm so glad you reached out", "You're not alone"
                - Validate their pain without minimizing it
                - Show genuine care for their safety and wellbeing
                - Remain calm, reassuring, and deeply compassionate
                - Provide immediate emotional comfort and grounding
                - Focus on safety and emotional stabilization
                - Emphasize their value and worth as a person
                
                CRITICAL SAFETY: You are NOT a crisis counselor or medical professional. Cannot provide professional crisis intervention.
                
                For suicidal thoughts, self-harm, or severe crisis, IMMEDIATELY direct to:
                ⚠️ EMERGENCY: Call 911
                ⚠️ National Suicide Prevention Lifeline: 988
                ⚠️ Crisis Text Line: Text HOME to 741741
                ⚠️ Local emergency room or mental health professional
                
                Provide emotional support while strongly encouraging immediate professional help. Safety is absolute priority. Keep responses compassionate but brief.'''
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
        Generate AI response synchronously using OpenAI ChatGPT with comprehensive error handling
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
            
            # Check client availability
            if not self.client:
                logger.error("OpenAI client not initialized")
                return self._get_safe_response(companion_type, "I'm experiencing technical difficulties. Please try again later.")
            
            # Get companion info
            companion_info = self.companion_types.get(companion_type, self.companion_types['priya'])
            system_prompt = companion_info.get('system_prompt', 'You are a helpful and empathetic AI companion.')
            
            # Build the conversation messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add session context if available
            if session_context and isinstance(session_context, str):
                try:
                    context_messages = session_context.split('\n')
                    for context_msg in context_messages[-6:]:  # Last 6 messages for context
                        if context_msg.strip():
                            if context_msg.startswith('User:'):
                                messages.append({"role": "user", "content": context_msg[5:].strip()})
                            elif context_msg.startswith('AI:'):
                                messages.append({"role": "assistant", "content": context_msg[3:].strip()})
                except Exception as context_error:
                    logger.warning(f"Error processing session context: {context_error}")
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # Generate response using OpenAI with error handling
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    timeout=30  # 30 second timeout
                )
                
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content and content.strip():
                        return content.strip()
                    else:
                        logger.warning("OpenAI returned empty content")
                        return self._get_safe_response(companion_type, "I want to respond thoughtfully. Could you help me understand better?")
                else:
                    logger.warning("OpenAI returned no choices")
                    return self._get_safe_response(companion_type, "I'm processing your message. Could you please rephrase or try again?")
                    
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}")
                # Check for specific API errors
                if "quota" in str(api_error).lower() or "limit" in str(api_error).lower():
                    return self._get_safe_response(companion_type, "I'm currently at capacity. Please try again in a moment.")
                elif "timeout" in str(api_error).lower():
                    return self._get_safe_response(companion_type, "I'm taking longer than usual to respond. Please try again.")
                else:
                    return self._get_safe_response(companion_type, "I'm having trouble connecting right now, but I'm still here for you.")
                
        except Exception as e:
            logger.error(f"Critical error in OpenAI generate_response_sync: {str(e)}")
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
openai_service = OpenAIService()