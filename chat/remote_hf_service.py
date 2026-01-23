"""
Remote Hugging Face API Service
Calls HF Space for model predictions instead of loading locally
"""

import logging
import requests
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
    
    def chat(self, message: str) -> Dict:
        """
        Generate chat response using remote model
        
        Args:
            message: User message
            
        Returns:
            Response dict with response text, emotion, confidence, etc.
        """
        prediction = self.predict_emotion(message)
        
        # Generate response based on emotion
        emotion = prediction.get("emotion", "neutral")
        is_crisis = prediction.get("is_crisis", False)
        confidence = prediction.get("confidence", 0.0)
        
        # Crisis response
        if is_crisis:
            response_text = "I'm really concerned about what you're saying. Your safety is the most important thing right now. Please reach out to a counselor immediately or contact a crisis helpline. You don't have to face this alone."
        else:
            # Emotion-based responses
            responses = {
                "joy": "I'm so glad to hear you're feeling positive! What's making you feel this way?",
                "sadness": "I hear that you're going through a tough time. It's okay to feel sad. Would you like to talk about what's bothering you?",
                "anger": "It sounds like something is really frustrating you. I'm here to listen. What's been making you angry?",
                "fear": "I understand you're feeling anxious or worried. Those feelings are valid. What's causing you to feel this way?",
                "surprise": "That sounds unexpected! How are you processing this?",
                "disgust": "I hear that something is really bothering you. Would you like to talk about it?",
                "neutral": "I'm here to listen. How can I help you today?"
            }
            
            response_text = responses.get(emotion, responses["neutral"])
        
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
