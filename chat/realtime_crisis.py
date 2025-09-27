"""
Real-time crisis detection and alert system.
Integrates with WebSocket consumers to provide immediate crisis response.
"""

import re
from typing import List, Dict, Any
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ChatSession, Message
from crisis.models import CrisisAlert
from .websocket_utils import send_crisis_notification, send_real_time_notification

User = get_user_model()


class CrisisDetector:
    """
    Advanced crisis detection system with real-time alerting.
    Analyzes messages for crisis indicators and triggers immediate responses.
    """
    
    # Crisis keywords with severity levels (1-10)
    CRISIS_KEYWORDS = {
        'critical': {
            'suicide': 10,
            'kill myself': 10,
            'end my life': 10,
            'want to die': 9,
            'better off dead': 9,
            'end it all': 9,
            'no point living': 8,
            'can\'t go on': 8,
        },
        'high': {
            'self harm': 7,
            'hurt myself': 7,
            'cutting': 7,
            'overdose': 8,
            'hopeless': 6,
            'worthless': 6,
            'alone': 4,
            'trapped': 6,
        },
        'medium': {
            'depressed': 5,
            'anxious': 4,
            'panic': 5,
            'scared': 4,
            'worried': 3,
            'stressed': 3,
        },
        'low': {
            'sad': 2,
            'tired': 2,
            'upset': 2,
            'frustrated': 2,
        }
    }
    
    # Crisis patterns (regex)
    CRISIS_PATTERNS = [
        (r'\b(?:i\s+)?(?:want|need|have)\s+to\s+(?:die|kill\s+myself)\b', 10),
        (r'\b(?:i\s+)?(?:can\'t|cannot)\s+(?:take|handle)\s+(?:this|it)\s+anymore\b', 8),
        (r'\b(?:nobody|no\s+one)\s+(?:cares|loves|understands)\s+(?:me|about\s+me)\b', 7),
        (r'\bthinking\s+about\s+(?:suicide|killing\s+myself|ending\s+it)\b', 9),
        (r'\b(?:i\s+)?(?:don\'t|do\s+not)\s+(?:want|deserve)\s+to\s+live\b', 9),
    ]
    
    @classmethod
    def analyze_message(cls, message_content: str, user_id: int = None) -> Dict[str, Any]:
        """
        Analyze message content for crisis indicators.
        
        Args:
            message_content (str): The message to analyze
            user_id (int): User ID for context
            
        Returns:
            Dict containing crisis analysis results
        """
        message_lower = message_content.lower()
        detected_keywords = []
        max_severity = 0
        crisis_level = 0
        
        # Check keywords
        for category, keywords in cls.CRISIS_KEYWORDS.items():
            for keyword, severity in keywords.items():
                if keyword in message_lower:
                    detected_keywords.append({
                        'keyword': keyword,
                        'severity': severity,
                        'category': category
                    })
                    max_severity = max(max_severity, severity)
        
        # Check patterns
        for pattern, severity in cls.CRISIS_PATTERNS:
            if re.search(pattern, message_lower):
                detected_keywords.append({
                    'pattern': pattern,
                    'severity': severity,
                    'category': 'pattern'
                })
                max_severity = max(max_severity, severity)
        
        # Calculate overall crisis level
        if max_severity >= 8:
            crisis_level = max_severity
        elif max_severity >= 6:
            crisis_level = max_severity - 1
        elif max_severity >= 4:
            crisis_level = max_severity - 2
        else:
            crisis_level = max_severity
        
        return {
            'is_crisis': crisis_level >= 5,
            'crisis_level': crisis_level,
            'severity': max_severity,
            'detected_keywords': detected_keywords,
            'requires_immediate_attention': crisis_level >= 8,
            'requires_counselor': crisis_level >= 6,
            'recommendation': cls._get_recommendation(crisis_level),
        }
    
    @classmethod
    def _get_recommendation(cls, crisis_level: int) -> str:
        """Get recommendation based on crisis level"""
        if crisis_level >= 8:
            return "Immediate intervention required - connect with crisis counselor"
        elif crisis_level >= 6:
            return "High concern - recommend speaking with counselor"
        elif crisis_level >= 4:
            return "Moderate concern - provide support resources"
        elif crisis_level >= 2:
            return "Low concern - continue monitoring"
        else:
            return "No immediate concern detected"
    
    @classmethod
    def process_crisis_message(cls, message: Message, analysis: Dict[str, Any]) -> CrisisAlert:
        """
        Process a message that contains crisis indicators.
        Creates crisis alert and triggers real-time notifications.
        
        Args:
            message: The Message object
            analysis: Crisis analysis results
            
        Returns:
            CrisisAlert object
        """
        # Create crisis alert
        alert = CrisisAlert.objects.create(
            user=message.sender,
            crisis_level=analysis['crisis_level'],
            description=f"Crisis detected in chat message: {message.content[:200]}...",
            detected_via='chat',
            status='open',
            chat_session=message.session if hasattr(message, 'session') else None,
            message=message,
            keywords_detected=analysis['detected_keywords'],
            requires_immediate_attention=analysis['requires_immediate_attention']
        )
        
        # Send real-time crisis alert to monitoring staff
        cls._send_crisis_alerts(alert, analysis)
        
        # Notify the user with supportive message
        cls._send_user_support_notification(message.sender, analysis)
        
        # Update chat session crisis status
        if hasattr(message, 'session') and message.session:
            session = message.session
            session.crisis_level = max(session.crisis_level, analysis['crisis_level'])
            session.save()
        
        return alert
    
    @classmethod
    def _send_crisis_alerts(cls, alert: CrisisAlert, analysis: Dict[str, Any]):
        """Send crisis alerts to monitoring staff"""
        # Send to crisis monitoring WebSocket
        send_crisis_notification(
            alert.user,
            alert.crisis_level,
            alert.description,
            'automated'
        )
        
        # Send urgent notification to all counselors if critical
        if analysis['requires_immediate_attention']:
            counselors = User.objects.filter(role='counselor', is_active=True)
            for counselor in counselors:
                send_real_time_notification(
                    counselor.id,
                    'urgent_crisis_alert',
                    'Critical Crisis Alert',
                    f'User {alert.user.first_name} requires immediate attention',
                    {
                        'alert_id': str(alert.id),
                        'user_id': alert.user.id,
                        'crisis_level': alert.crisis_level,
                        'timestamp': alert.created_at.isoformat()
                    }
                )
    
    @classmethod
    def _send_user_support_notification(cls, user, analysis: Dict[str, Any]):
        """Send supportive notification to user"""
        if analysis['crisis_level'] >= 8:
            message = "I'm very concerned about you. You're not alone, and help is available. Would you like me to connect you with a crisis counselor right now?"
        elif analysis['crisis_level'] >= 6:
            message = "I hear that you're going through a difficult time. Would you like to speak with a counselor who can provide additional support?"
        elif analysis['crisis_level'] >= 4:
            message = "It sounds like you're dealing with some challenges. Remember that support is available if you need it."
        else:
            message = "Thank you for sharing. I'm here to listen and support you."
        
        send_real_time_notification(
            user.id,
            'support_message',
            'MANAS Support',
            message,
            {
                'crisis_support': True,
                'crisis_level': analysis['crisis_level'],
                'resources_available': True
            }
        )


class RealTimeChatManager:
    """
    Manager for real-time chat functionality.
    Handles message processing, AI responses, and crisis detection.
    """
    
    @staticmethod
    def process_incoming_message(session_id: str, sender_id: int, content: str) -> Dict[str, Any]:
        """
        Process an incoming chat message with crisis detection.
        
        Args:
            session_id: Chat session ID
            sender_id: User ID of sender
            content: Message content
            
        Returns:
            Dict with processing results
        """
        try:
            # Get session and user
            session = ChatSession.objects.get(id=session_id)
            sender = User.objects.get(id=sender_id)
            
            # Create message
            message = Message.objects.create(
                session=session,
                sender=sender,
                content=content,
                message_type='text'
            )
            
            # Analyze for crisis
            crisis_analysis = CrisisDetector.analyze_message(content, sender_id)
            
            # Process crisis if detected
            crisis_alert = None
            if crisis_analysis['is_crisis']:
                crisis_alert = CrisisDetector.process_crisis_message(message, crisis_analysis)
            
            # Generate AI response if needed
            ai_response = None
            if session.session_type == 'ai':
                ai_response = RealTimeChatManager._generate_ai_response(
                    session, message, crisis_analysis
                )
            
            return {
                'success': True,
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'sender': sender_id,
                    'timestamp': message.created_at.isoformat(),
                    'crisis_detected': crisis_analysis['is_crisis'],
                    'crisis_level': crisis_analysis['crisis_level']
                },
                'crisis_analysis': crisis_analysis,
                'crisis_alert': str(crisis_alert.id) if crisis_alert else None,
                'ai_response': ai_response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _generate_ai_response(session: ChatSession, user_message: Message, crisis_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI response based on message and crisis analysis.
        
        This is a placeholder - will be enhanced with actual AI integration.
        """
        if crisis_analysis['is_crisis']:
            if crisis_analysis['crisis_level'] >= 8:
                ai_content = "I'm really concerned about what you've shared. Your safety is the most important thing right now. I'd like to connect you with a crisis counselor who can provide immediate support. You don't have to go through this alone."
            elif crisis_analysis['crisis_level'] >= 6:
                ai_content = "I can hear that you're going through a very difficult time. It takes courage to reach out. Would you like me to help you connect with a counselor who specializes in these situations?"
            else:
                ai_content = "Thank you for sharing what you're experiencing. It sounds challenging, and I want you to know that support is available. How are you feeling right now?"
        else:
            # Generate contextual response based on message content
            content_lower = user_message.content.lower()
            
            if any(word in content_lower for word in ['anxious', 'anxiety', 'worried']):
                ai_content = "I understand you're feeling anxious. Anxiety can be really overwhelming. What's been on your mind lately that's causing these feelings?"
            elif any(word in content_lower for word in ['sad', 'depressed', 'down']):
                ai_content = "I hear that you're feeling down. Those feelings are valid and it's okay to not be okay sometimes. Would you like to talk about what's been affecting your mood?"
            elif any(word in content_lower for word in ['stressed', 'pressure', 'overwhelmed']):
                ai_content = "It sounds like you're under a lot of pressure right now. Stress can be really challenging to manage. What's been the biggest source of stress for you lately?"
            else:
                ai_content = "Thank you for sharing that with me. I'm here to listen and support you. Can you tell me more about how you're feeling?"
        
        # Create AI response message
        ai_message = Message.objects.create(
            session=session,
            content=ai_content,
            message_type='text',
            is_ai_response=True
        )
        
        return {
            'id': str(ai_message.id),
            'content': ai_message.content,
            'timestamp': ai_message.created_at.isoformat(),
            'is_ai_response': True,
            'crisis_support': crisis_analysis['is_crisis']
        }


# Utility functions for integration
def detect_crisis_in_message(message_content: str, user_id: int = None) -> Dict[str, Any]:
    """
    Standalone function to detect crisis in message content.
    Can be used by consumers or other parts of the system.
    """
    return CrisisDetector.analyze_message(message_content, user_id)


def process_real_time_message(session_id: str, sender_id: int, content: str) -> Dict[str, Any]:
    """
    Standalone function to process real-time messages.
    Can be called from WebSocket consumers.
    """
    return RealTimeChatManager.process_incoming_message(session_id, sender_id, content)