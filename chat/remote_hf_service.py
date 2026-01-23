"""
Remote Hugging Face API Service
Calls HF Space for model predictions instead of loading locally
"""

import logging
import requests
import random
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RemoteHFService:
    """Service to call Hugging Face Space API for predictions"""
    
    def __init__(self, api_url: str = None):
        """
        Initialize remote HF service
        
        Args:
            api_url: URL of your HF Space (e.g., https://omshukla16-manas-edu.hf.space)
        """
        self.api_url = api_url or "https://omshukla16-manas-edu.hf.space"
        self.predict_endpoint = f"{self.api_url}/predict"
        self.chat_endpoint = f"{self.api_url}/chat"
        self.health_endpoint = f"{self.api_url}/health"
        
        logger.info(f"🌐 Remote HF Service initialized: {self.api_url}")
    
    def is_available(self) -> bool:
        """Check if the HF Space API is available"""
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HF Space not available: {e}")
            return False
    
    def predict_emotion(self, text: str) -> Dict:
        """
        Get emotion prediction from HF Space
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict with emotion, confidence, is_crisis, all_scores
        """
        try:
            response = requests.post(
                self.predict_endpoint,
                json={"text": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"HF API request failed: {e}")
            return {
                "emotion": "neutral",
                "confidence": 0.0,
                "is_crisis": False,
                "all_scores": []
            }
    
    def chat(self, message: str, context=None) -> Dict:
        """
        Generate chat response using remote model
        
        Args:
            message: User message
            context: Conversation history (list of dicts with role and content)
            
        Returns:
            Response dict with response text, emotion, confidence, etc.
        """
        try:
            # Try to use the /chat endpoint first (if available)
            payload = {
                "message": message,
                "conversation_history": context if context else [],
                "max_length": 100
            }
            
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("response", ""),
                    "emotion": data.get("emotion", "neutral"),
                    "confidence": data.get("confidence", 0.5),
                    "is_crisis": False,
                    "intensity": "high" if data.get("confidence", 0) > 0.7 else "medium",
                    "suggested_actions": []
                }
            
            # Fallback to emotion detection + template if /chat not available
            logger.warning(f"Chat endpoint returned {response.status_code}, using fallback")
            
        except Exception as e:
            logger.warning(f"Chat endpoint failed: {e}, using fallback")
        
        # FALLBACK: Use emotion detection + templates
        prediction = self.predict_emotion(message)
        
        # Generate response based on emotion
        emotion = prediction.get("emotion", "neutral")
        is_crisis = prediction.get("is_crisis", False)
        confidence = prediction.get("confidence", 0.0)
        
        # Crisis response
        if is_crisis:
            response_text = "I'm really concerned about what you're saying. Your safety is the most important thing right now. Please reach out to a counselor immediately or contact a crisis helpline. You don't have to face this alone."
        else:
            # Context-aware responses based on emotion AND conversation
            message_lower = message.lower()
            
            # Count how many messages in conversation (for variety)
            conversation_depth = len(context) if context else 0
            
            # Detect topics for better responses
            if emotion == "sadness":
                if any(word in message_lower for word in ['bullied', 'bully', 'hurt', 'mean']):
                    responses = [
                        "I'm really sorry you're experiencing bullying. That must be incredibly difficult. Remember that bullying says more about the bully than about you. Have you talked to anyone about this - a counselor, teacher, or trusted adult?",
                        "Bullying is never okay, and I'm sorry you're going through this. It takes a lot of courage to share this. How are you coping with it right now?",
                        "What you're experiencing sounds really painful. No one deserves to be bullied. Have you been able to talk to anyone who can help - maybe a counselor or teacher?"
                    ]
                    response_text = random.choice(responses)
                elif any(word in message_lower for word in ['friend', 'friends', 'alone', 'lonely']):
                    responses = [
                        "It's really hard when friendships feel difficult or when you feel alone. Those feelings are completely valid. What's been happening with your friends?",
                        "Feeling lonely can be so tough. I want you to know that what you're feeling matters. Would you like to share more about what's going on with your friendships?",
                        "Friendship challenges can really hurt. It sounds like you're going through something difficult. Tell me more about what's been happening."
                    ]
                    response_text = random.choice(responses)
                else:
                    responses = [
                        "I hear that you're going through a tough time. It's okay to feel sad. Would you like to talk more about what's bothering you?",
                        "It sounds like something is weighing on you. I'm here to listen without judgment. What's been on your mind?",
                        "That sounds really hard. Your feelings are valid, and I'm here with you. What would help you feel supported right now?"
                    ]
                    response_text = random.choice(responses)
            
            elif emotion == "anger":
                responses = [
                    "I can sense your frustration, and it's completely okay to feel angry. Sometimes anger protects us from deeper hurt. What happened that made you feel this way?",
                    "It sounds like something really upset you. Anger is a valid emotion. Would you like to talk about what's frustrating you?",
                    "I hear the frustration in what you're sharing. Let's talk through it - what's been making you feel this way?"
                ]
                response_text = random.choice(responses)
            
            elif emotion == "fear":
                responses = [
                    "I understand you're feeling anxious or worried. Those feelings are valid. Taking things one step at a time can help. What's worrying you most right now?",
                    "Anxiety can feel overwhelming, but you're not alone in this. Let's work through it together. What's making you feel anxious?",
                    "I hear that you're feeling worried. That's completely understandable. Would you like to share what's on your mind?"
                ]
                response_text = random.choice(responses)
            
            elif emotion == "joy":
                responses = [
                    "I'm so glad to hear you're feeling positive! It's wonderful to celebrate these moments. What's making you feel this way?",
                    "That's great to hear! It's important to embrace these good feelings. Tell me more!",
                    "Your positive energy is wonderful! What's brought about this happiness?"
                ]
                response_text = random.choice(responses)
            
            else:
                # Neutral or other emotions - vary responses based on conversation depth
                if conversation_depth == 0:
                    responses = [
                        "Hello! I'm MANAS, your mental health support companion. I'm here to listen and support you. What's on your mind today?",
                        "Hi there! Thanks for reaching out. I'm here to listen without judgment. How can I support you today?",
                        "Welcome! I'm here as your mental health companion. Feel free to share what's on your mind - this is a safe space."
                    ]
                elif conversation_depth < 3:
                    responses = [
                        "I'm listening. Tell me more about what you're experiencing.",
                        "I hear you. Can you share more about what's going on?",
                        "Thanks for sharing. How are you feeling about all of this?",
                        "I'm here with you. What else would you like to talk about?"
                    ]
                else:
                    # Deeper in conversation - show continuity
                    responses = [
                        "I appreciate you opening up to me. How are you feeling about everything we've discussed?",
                        "It takes courage to keep sharing. What else is on your mind?",
                        "I'm glad you're talking through this with me. How can I best support you right now?",
                        "Thank you for trusting me with your thoughts. What would be most helpful for you in this moment?"
                    ]
                response_text = random.choice(responses)
        
        return {
            "response": response_text,
            "emotion": emotion,
            "confidence": confidence,
            "is_crisis": is_crisis,
            "intensity": "high" if confidence > 0.7 else "medium",
            "suggested_actions": []
        }


# Global instance
_remote_service = None

def get_remote_hf_service() -> RemoteHFService:
    """Get singleton instance of remote HF service"""
    global _remote_service
    if _remote_service is None:
        _remote_service = RemoteHFService()
    return _remote_service
