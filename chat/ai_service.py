"""
AI Chatbot Service for MANAS Platform
Handles Gemini AI integration with three specialized chatbot personalities:
- Hybrid: Balanced emotional support and practical advice
- Listener: Focused on empathetic listening and validation
- Practical Advisor: Solution-oriented with actionable guidance
"""

import json
import re
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async
import logging

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .models import ChatSession, Message, AIPersonality, ChatAnalytics

logger = logging.getLogger(__name__)


class GeminiAIService:
    """
    Service class for handling Gemini AI interactions with multiple personality models
    """
    
    def __init__(self):
        self.primary_api_key = settings.GEMINI_API_KEY
        self.backup_api_key = settings.GEMINI_API_KEY_BACKUP
        self.model_name = settings.GEMINI_MODEL
        self.advanced_model_name = settings.GEMINI_MODEL_ADVANCED
        self.current_api_key = self.primary_api_key
        self.chatbot_models = settings.AI_CHATBOT_MODELS
        self.crisis_keywords = settings.CRISIS_KEYWORDS
        self.crisis_threshold = settings.CRISIS_ESCALATION_THRESHOLD
        
        # Initialize Gemini AI
        if genai and self.current_api_key:
            genai.configure(api_key=self.current_api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.advanced_model = genai.GenerativeModel(self.advanced_model_name)
        else:
            logger.error("Gemini AI not available or API key not configured")
            self.model = None
            self.advanced_model = None
    
    def switch_to_backup_api(self):
        """Switch to backup API key if primary fails"""
        if self.backup_api_key and self.current_api_key != self.backup_api_key:
            self.current_api_key = self.backup_api_key
            genai.configure(api_key=self.current_api_key)
            logger.info("Switched to backup Gemini API key")
            return True
        return False
    
    def analyze_crisis_indicators(self, message_content: str) -> Dict:
        """Analyze message for crisis indicators"""
        crisis_score = 0
        detected_keywords = []
        
        message_lower = message_content.lower()
        
        # Check for direct crisis keywords
        for keyword in self.crisis_keywords:
            if keyword.lower() in message_lower:
                detected_keywords.append(keyword)
                crisis_score += 2
        
        # Additional patterns
        crisis_patterns = [
            r'\b(want to|going to|plan to)\s+(die|kill|hurt)\b',
            r'\b(suicide|suicidal)\b',
            r'\b(end it all|end everything)\b',
            r'\b(can\'t take it|can\'t handle)\b',
            r'\b(no hope|hopeless|worthless)\b',
        ]
        
        for pattern in crisis_patterns:
            if re.search(pattern, message_lower):
                crisis_score += 1.5
        
        # Normalize score to 0-10 scale
        crisis_score = min(crisis_score, 10)
        
        return {
            'crisis_score': crisis_score,
            'keywords_detected': detected_keywords,
            'requires_intervention': crisis_score >= self.crisis_threshold,
            'is_crisis': crisis_score >= 5
        }
    
    def get_personality_context(self, chatbot_type: str, session_history: List[Dict] = None) -> str:
        """Get personality-specific context for the AI model"""
        if chatbot_type not in self.chatbot_models:
            chatbot_type = 'HYBRID'  # Default fallback
        
        personality = self.chatbot_models[chatbot_type]
        
        context = f"""
{personality['personality_prompt']}

IMPORTANT GUIDELINES:
- Always prioritize user safety and mental health
- If you detect crisis indicators (suicide, self-harm), respond with immediate support and suggest professional help
- Be culturally sensitive and inclusive
- Keep responses concise but meaningful (100-300 words typically)
- Use the user's name when appropriate to personalize the conversation
- Remember this is a mental health support platform - be professional yet warm
- If user asks about medication or clinical diagnosis, refer them to qualified professionals

Your specialization: {personality['specialization']}
Communication tone: {personality['tone']}
"""
        
        if session_history:
            context += "\n\nCONVERSATION CONTEXT:\n"
            for msg in session_history[-5:]:  # Last 5 messages for context
                role = "User" if msg['sender_type'] == 'user' else "You"
                context += f"{role}: {msg['content']}\n"
        
        return context
    
    async def generate_response(
        self, 
        user_message: str, 
        chatbot_type: str,
        session: ChatSession,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Generate AI response using Gemini with personality-specific context
        """
        try:
            # Analyze crisis indicators first
            crisis_analysis = self.analyze_crisis_indicators(user_message)
            
            # Get personality context
            personality_context = self.get_personality_context(chatbot_type, conversation_history)
            
            # Choose model based on crisis level
            model_to_use = self.advanced_model if crisis_analysis['is_crisis'] else self.model
            
            if not model_to_use:
                return self._get_fallback_response(user_message, crisis_analysis)
            
            # Prepare the full prompt
            full_prompt = f"""
{personality_context}

CURRENT USER MESSAGE: {user_message}

Please respond as {self.chatbot_models[chatbot_type]['name']} with appropriate emotional support and guidance.
"""
            
            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync_response, model_to_use, full_prompt
            )
            
            if response is None:
                # Try backup API if primary failed
                if self.switch_to_backup_api():
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, self._generate_sync_response, model_to_use, full_prompt
                    )
            
            if response is None:
                return self._get_fallback_response(user_message, crisis_analysis)
            
            # Post-process response for crisis situations
            if crisis_analysis['requires_intervention']:
                response = self._add_crisis_support_resources(response)
            
            return {
                'content': response,
                'chatbot_type': chatbot_type,
                'model_used': self.model_name,
                'crisis_analysis': crisis_analysis,
                'timestamp': timezone.now(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return self._get_fallback_response(user_message, crisis_analysis, str(e))
    
    def _generate_sync_response(self, model, prompt: str) -> Optional[str]:
        """Synchronous response generation for use in executor"""
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None
        return None
    
    def _add_crisis_support_resources(self, response: str) -> str:
        """Add crisis support resources to response when needed"""
        crisis_addendum = """

🚨 **IMMEDIATE SUPPORT AVAILABLE:**
If you're having thoughts of self-harm or suicide, please reach out immediately:
• National Suicide Prevention Lifeline: 988 (US)
• Crisis Text Line: Text HOME to 741741
• Emergency Services: 911
• Or speak with a counselor here on MANAS - we're here 24/7

You're not alone, and help is always available. 💙
"""
        return response + crisis_addendum
    
    def _get_fallback_response(self, user_message: str, crisis_analysis: Dict, error: str = None) -> Dict:
        """Generate fallback response when AI is unavailable"""
        if crisis_analysis['requires_intervention']:
            content = """I understand you're going through a very difficult time right now. While I'm experiencing some technical difficulties, 
I want you to know that immediate help is available. Please consider reaching out to a crisis hotline or emergency services, 
or connect with one of our human counselors immediately. Your safety and wellbeing are our top priority. 🚨💙"""
        else:
            content = """I'm here to listen and support you. I'm experiencing some technical difficulties right now, 
but please know that your feelings and concerns are valid. Would you like to connect with one of our human counselors, 
or would you like to try again in a moment? I'm committed to being here for you. 💙"""
        
        return {
            'content': content,
            'chatbot_type': 'HYBRID',
            'model_used': 'fallback',
            'crisis_analysis': crisis_analysis,
            'timestamp': timezone.now(),
            'success': False,
            'error': error
        }
    
    async def analyze_conversation_sentiment(self, messages: List[str]) -> Dict:
        """Analyze overall conversation sentiment and emotional trends"""
        try:
            if not self.model or not messages:
                return {'sentiment': 'neutral', 'confidence': 0.5}
            
            conversation_text = ' '.join(messages[-10:])  # Last 10 messages
            
            prompt = f"""
Analyze the emotional sentiment and mental health indicators in this conversation:

{conversation_text}

Provide a JSON response with:
1. overall_sentiment: (positive/neutral/negative)
2. confidence: (0.0 to 1.0)
3. dominant_emotions: (array of emotions detected)
4. mental_health_concerns: (array of any concerns identified)
5. improvement_indicators: (any positive changes noted)

Response format: {{"overall_sentiment": "...", "confidence": 0.0, "dominant_emotions": [], "mental_health_concerns": [], "improvement_indicators": []}}
"""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync_response, self.model, prompt
            )
            
            if response:
                # Try to parse JSON response
                try:
                    return json.loads(response)
                except:
                    # Fallback parsing
                    return {'sentiment': 'neutral', 'confidence': 0.5, 'raw_response': response}
            
            return {'sentiment': 'neutral', 'confidence': 0.5}
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {'sentiment': 'neutral', 'confidence': 0.5, 'error': str(e)}
    
    async def generate_session_summary(self, session: ChatSession) -> str:
        """Generate AI summary of the chat session"""
        try:
            messages = await sync_to_async(list)(
                session.messages.order_by('created_at').values_list('content', 'message_type')
            )
            
            if not messages or not self.model:
                return "Session summary unavailable."
            
            # Format conversation for summary
            conversation = []
            for content, msg_type in messages:
                role = "User" if msg_type == 'user' else "AI Assistant"
                conversation.append(f"{role}: {content}")
            
            conversation_text = '\n'.join(conversation)
            
            prompt = f"""
Analyze this mental health support conversation and provide a professional summary:

{conversation_text}

Provide a summary including:
1. Main topics discussed
2. User's primary concerns or challenges
3. Emotional state and any changes during conversation
4. Support strategies used
5. Any follow-up recommendations
6. Crisis indicators (if any)

Keep the summary professional, empathetic, and clinically appropriate for mental health records.
"""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync_response, self.advanced_model or self.model, prompt
            )
            
            return response if response else "Session summary could not be generated."
            
        except Exception as e:
            logger.error(f"Error generating session summary: {str(e)}")
            return f"Session summary error: {str(e)}"
    
    def get_available_chatbots(self) -> List[Dict]:
        """Get list of available chatbot personalities"""
        chatbots = []
        for key, config in self.chatbot_models.items():
            chatbots.append({
                'id': key,
                'name': config['name'],
                'description': config['description'],
                'specialization': config['specialization'],
                'avatar_emoji': config['avatar_emoji'],
                'color_theme': config['color_theme'],
                'is_available': bool(self.model)
            })
        return chatbots
    
    async def create_ai_personality_records(self):
        """Create/update AIPersonality records in database"""
        for key, config in self.chatbot_models.items():
            personality, created = await sync_to_async(AIPersonality.objects.get_or_create)(
                name=config['name'],
                defaults={
                    'description': config['description'],
                    'personality_prompt': config['personality_prompt'],
                    'specialization': config['specialization'],
                    'tone': config['tone'],
                    'response_style': 'conversational',
                    'is_active': True,
                    'is_crisis_capable': config['crisis_capable'],
                    'color_theme': config['color_theme']
                }
            )
            
            if not created:
                # Update existing personality
                personality.description = config['description']
                personality.personality_prompt = config['personality_prompt']
                personality.specialization = config['specialization']
                personality.tone = config['tone']
                personality.is_crisis_capable = config['crisis_capable']
                personality.color_theme = config['color_theme']
                await sync_to_async(personality.save)()


    def generate_response_sync(self, user_message: str, chatbot_type: str, session, conversation_history: list = None) -> dict:
        """Synchronous wrapper for generate_response"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_response(user_message, chatbot_type, session, conversation_history)
        )
    
    def generate_session_summary_sync(self, session) -> str:
        """Synchronous wrapper for generate_session_summary"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_session_summary(session)
        )
    
    def analyze_conversation_sentiment_sync(self, messages: list) -> dict:
        """Synchronous wrapper for analyze_conversation_sentiment"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.analyze_conversation_sentiment(messages)
        )


# Global service instance
gemini_service = GeminiAIService()