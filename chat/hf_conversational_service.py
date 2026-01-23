"""
HuggingFace Inference API - Mental Health Conversational Chatbot
Uses free HuggingFace API (no data storage, privacy-friendly)
Model: microsoft/DialoGPT-medium or mental health specific models
"""

import logging
import requests
import os
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class HFConversationalService:
    """
    HuggingFace Inference API for mental health conversations
    Privacy-friendly: Data processed but not stored by HuggingFace
    """
    
    def __init__(self):
        """Initialize HuggingFace Inference API client"""
        logger.info("🤗 Initializing HuggingFace Conversational Service...")
        
        # Get API token from environment
        self.api_token = os.environ.get('HUGGINGFACE_API_TOKEN', '')
        
        # Choose model based on availability
        # All models are confirmed available and free on HuggingFace
        
        self.models = {
            'conversational': 'microsoft/DialoGPT-medium',           # 117M params - Natural chat
            'blenderbot': 'facebook/blenderbot-400M-distill',        # 400M params - Empathetic
            'instruction': 'meta-llama/Llama-2-7b-chat-hf',         # 7B params - Advanced (may need auth)
        }
        
        # Use BlenderBot as default (more empathetic for mental health)
        self.current_model = self.models['blenderbot']
        self.api_url = f"https://api-inference.huggingface.co/models/{self.current_model}"
        
        # Conversation context (for multi-turn conversations)
        self.max_context_length = 5  # Keep last 5 exchanges
        
        # Mental health prompt engineering
        self.system_prompt = (
            "You are MANAS, an empathetic AI mental health companion for students. "
            "You provide emotional support, active listening, and evidence-based coping strategies. "
            "You are compassionate, non-judgmental, and validate feelings. "
            "You detect crisis situations and provide appropriate resources. "
            "You never diagnose or prescribe medication - you support and guide towards professional help when needed."
        )
        
        logger.info(f"✅ Using model: {self.current_model}")
        logger.info(f"✅ API token configured: {bool(self.api_token)}")
    
    def generate_response(self, user_message, conversation_history=None, companion_type='supportive'):
        """
        Generate conversational response using HuggingFace API
        
        Args:
            user_message (str): User's current message
            conversation_history (list): Previous conversation context
            companion_type (str): Companion personality type
            
        Returns:
            dict: Response with generated text and metadata
        """
        if not user_message or not user_message.strip():
            return {
                'response': "I'm here to listen. What's on your mind?",
                'confidence': 1.0,
                'model': 'template'
            }
        
        # Check if API token is available
        if not self.api_token:
            logger.warning("No HuggingFace API token - using template responses")
            return self._get_template_response(user_message)
        
        try:
            # Build conversation context
            context = self._build_context(user_message, conversation_history, companion_type)
            
            # Call HuggingFace Inference API
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": context,
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True,
                    "use_cache": True
                }
            }
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract generated text
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '').strip()
                elif isinstance(result, dict):
                    generated_text = result.get('generated_text', '').strip()
                else:
                    generated_text = ''
                
                # Clean up response
                generated_text = self._clean_response(generated_text, user_message)
                
                if generated_text:
                    return {
                        'response': generated_text,
                        'confidence': 0.85,
                        'model': self.current_model,
                        'source': 'huggingface_api'
                    }
            
            # If API fails, fallback to templates
            logger.warning(f"HuggingFace API error: {response.status_code}")
            return self._get_template_response(user_message)
            
        except requests.exceptions.Timeout:
            logger.error("HuggingFace API timeout")
            return self._get_template_response(user_message)
        except Exception as e:
            logger.error(f"HuggingFace API error: {e}")
            return self._get_template_response(user_message)
    
    def _build_context(self, user_message, conversation_history, companion_type):
        """Build conversation context with system prompt"""
        
        # Personality variations
        personalities = {
            'supportive': "You are warm, empathetic, and validating. You focus on emotional support.",
            'analytical': "You are logical, structured, and solution-oriented. You help break down problems.",
            'mindful': "You are calm, present-focused, and teach mindfulness techniques."
        }
        
        personality = personalities.get(companion_type, personalities['supportive'])
        
        # Build context string
        context = f"{self.system_prompt} {personality}\n\n"
        
        # Add conversation history (last few exchanges)
        if conversation_history:
            recent_history = conversation_history[-self.max_context_length:]
            for msg in recent_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    context += f"Student: {content}\n"
                elif role == 'assistant':
                    context += f"MANAS: {content}\n"
        
        # Add current message
        context += f"Student: {user_message}\nMANAS:"
        
        return context
    
    def _clean_response(self, response, user_message):
        """Clean up generated response"""
        if not response:
            return ""
        
        # Remove repetitions of user message
        response = response.replace(user_message, '').strip()
        
        # Remove common artifacts
        response = response.replace('Student:', '').replace('MANAS:', '').strip()
        
        # Remove leading/trailing quotes
        response = response.strip('"\'')
        
        # Ensure proper punctuation
        if response and response[-1] not in '.!?':
            response += '.'
        
        # Add supportive emoji if appropriate
        if any(word in response.lower() for word in ['sorry', 'understand', 'here', 'support']):
            if '💙' not in response and '💚' not in response:
                response += ' 💙'
        
        return response
    
    def _get_template_response(self, user_message):
        """Fallback template-based responses when API is unavailable"""
        message_lower = user_message.lower()
        
        # Emotion-based templates
        if any(word in message_lower for word in ['anxious', 'worried', 'nervous', 'scared', 'afraid']):
            responses = [
                "I can sense you're feeling anxious. That's completely valid. Take a deep breath with me - what's worrying you most right now? 💙",
                "Anxiety can feel overwhelming. Remember, you're not alone in this. Would you like to talk about what's triggering these feelings? 🌿",
            ]
        elif any(word in message_lower for word in ['sad', 'depressed', 'down', 'unhappy', 'lonely']):
            responses = [
                "I'm really sorry you're feeling this way. Your emotions matter, and it's okay to not be okay. What's weighing on your heart? 💙",
                "That sounds really hard. I'm here to listen without judgment. Would you like to share more about what you're going through? 🌙",
            ]
        elif any(word in message_lower for word in ['angry', 'mad', 'frustrated', 'annoyed', 'upset']):
            responses = [
                "I hear your frustration, and those feelings are valid. Sometimes anger protects us from deeper hurt. What happened? 💪",
                "It sounds like something really upset you. Let's talk through it - getting feelings out can help. 🔥",
            ]
        elif any(word in message_lower for word in ['stress', 'overwhelmed', 'pressure', 'exam', 'deadline']):
            responses = [
                "That sounds incredibly stressful. When we're overwhelmed, taking it one step at a time helps. What's the most pressing thing right now? 💪",
                "Academic pressure is real. Remember to breathe and give yourself permission to take breaks. Let's tackle this together. 🌿",
            ]
        elif any(word in message_lower for word in ['happy', 'good', 'great', 'excited', 'joy']):
            responses = [
                "That's wonderful to hear! I'm so glad you're feeling good. What brought about this positive energy? 🌟✨",
                "Your happiness is contagious! It's important to celebrate these good moments. Tell me more! 💫",
            ]
        else:
            # General supportive responses
            responses = [
                "I'm here to listen and support you. Tell me more about what's on your mind. 💙",
                "Thanks for sharing with me. How are you feeling about this situation? I'm here for you. 🌟",
                "I hear you. It takes courage to open up. What would be most helpful for you right now? 💚",
            ]
        
        import random
        return {
            'response': random.choice(responses),
            'confidence': 0.75,
            'model': 'template',
            'source': 'fallback'
        }
    
    def switch_model(self, model_type='conversational'):
        """Switch between different HuggingFace models"""
        if model_type in self.models:
            self.current_model = self.models[model_type]
            self.api_url = f"https://api-inference.huggingface.co/models/{self.current_model}"
            logger.info(f"Switched to model: {self.current_model}")
            return True
        return False


# Global instance
hf_conversational_service = HFConversationalService()
