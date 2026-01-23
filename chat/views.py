"""
Chat Views - AI Mental Health Chatbot
Hybrid mode: Calls HF Space API for model inference
"""

import json
import logging
import os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatSession, Message, AIPersonality
from .serializers import ChatSessionDetailSerializer, MessageSerializer

# Check if we should use remote HF API or local models
USE_REMOTE_HF = os.environ.get('USE_REMOTE_HF', 'true').lower() == 'true'

if USE_REMOTE_HF:
    from .remote_hf_service import get_remote_hf_service
    chatbot_service = get_remote_hf_service()
    CHATBOT_TYPE = 'remote_hf'
    logger = logging.getLogger(__name__)
    logger.info("🌐 Using Remote HF Space API for AI predictions")
else:
    # Fallback to local NLP
    from .nlp_chatbot_service import NLPChatbotService
    chatbot_service = NLPChatbotService()
    CHATBOT_TYPE = 'nlp'
    logger = logging.getLogger(__name__)
    logger.info("🚀 Using Local NLP Chatbot")

from crisis.models import CrisisAlert, CrisisType

logger = logging.getLogger(__name__)


class ChatbotCompanionsView(APIView):
    """List available AI chatbot companions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get list of available MANAS AI companions"""
        try:
            companions = [
                {
                    'id': 'priya',
                    'name': 'Priya',
                    'title': 'Emotional Support Companion',
                    'description': 'Your empathetic friend for emotional support and listening',
                    'emoji': '💝',
                    'color': '#e91e63',
                    'specialization': 'emotional_support',
                    'provider': 'huggingface'
                },
                {
                    'id': 'arjun',
                    'name': 'Arjun',
                    'title': 'Academic Support Companion',
                    'description': 'Your study buddy for academic stress and guidance',
                    'emoji': '📚',
                    'color': '#4a90e2',
                    'specialization': 'academic_support',
                    'provider': 'nlp_local'
                },
                {
                    'id': 'vikram',
                    'name': 'Vikram',
                    'title': 'Crisis Support Companion',
                    'description': 'Your immediate support for crisis situations',
                    'emoji': '🚨',
                    'color': '#f44336',
                    'specialization': 'crisis_support',
                    'provider': 'nlp_local'
                }
            ]
            
            return Response({
                'success': True,
                'companions': companions,
                'provider': 'nlp_local',
                'message': 'NLP-based companions ready'
            })
        except Exception as e:
            logger.error(f"Error fetching companions: {e}")
            return Response({
                'success': False,
                'error': 'Failed to fetch companions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatSessionStartView(APIView):
    """Start a new chat session"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Start new AI chat session"""
        try:
            companion_type = request.data.get('companion', 'priya')
            initial_message = request.data.get('initial_message', '')
            
            # Create chat session
            session = ChatSession.objects.create(
                user=request.user,
                session_type='ai_chat',
                status='active',
                title=f"Chat with {companion_type.capitalize()}",
                language='en'
            )
            
            # If there's an initial message, process it
            if initial_message:
                response_data = self._process_message(session, initial_message, companion_type)
                
                return Response({
                    'success': True,
                    'session_id': str(session.id),
                    'message': 'Session started with initial message',
                    'ai_response': response_data
                })
            
            return Response({
                'success': True,
                'session_id': str(session.id),
                'message': 'Chat session started successfully'
            })
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _process_message(self, session, message_text, companion_type):
        """Process message and get AI response using Hugging Face"""
        # Save user message
        user_message = Message.objects.create(
            session=session,
            sender=session.user,
            message_type='user',
            content=message_text,
            timestamp=timezone.now()
        )
        
        # Get Hugging Face AI service
        hf_service = get_huggingface_service()
        
        # Get AI response
        response_data = hf_service.chat(message_text)
        
        # Save AI response
        ai_message = Message.objects.create(
            session=session,
            message_type='ai',
            content=response_data['response'],
            metadata={
                'emotion': response_data.get('emotion'),
                'confidence': response_data.get('confidence', 0.0),
                'intensity': response_data.get('intensity', 'medium'),
                'source': 'huggingface',
                'provider': 'huggingface',
                'companion': companion_type,
                'suggested_actions': response_data.get('suggested_actions', [])
            },
            timestamp=timezone.now()
        )
        
        # Check for crisis
        if response_data.get('is_crisis', False):
            self._handle_crisis(session, user_message, response_data)
        
        # Format response for compatibility
        return {
            'message': response_data['response'],
            'confidence': response_data.get('confidence', 0.0),
            'is_crisis': response_data.get('is_crisis', False),
            'source': 'huggingface',
            'provider': 'huggingface',
            'emotion': response_data.get('emotion'),
            'suggested_actions': response_data.get('suggested_actions', [])
        }


class ChatMessageSendView(APIView):
    """Send message in chat session"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Send message and get AI response"""
        try:
            session_id = request.data.get('session_id')
            message_text = request.data.get('message', '').strip()
            companion_type = request.data.get('companion', 'priya')
            
            if not message_text:
                return Response({
                    'success': False,
                    'error': 'Message cannot be empty'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get session
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
            
            if session.status != 'active':
                return Response({
                    'success': False,
                    'error': 'Chat session is not active'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save user message
            user_message = Message.objects.create(
                session=session,
                sender=request.user,
                message_type='user',
                content=message_text
            )
            
            # Get AI service response
            if CHATBOT_TYPE == 'remote_hf':
                response_data = chatbot_service.chat(message_text)
                model_used = 'remote_hf'
            else:
                response_data = chatbot_service.generate_response(message_text)
                model_used = 'nlp'
            
            # Save AI response
            ai_message = Message.objects.create(
                session=session,
                sender=request.user,  # Still requires a user for FK
                message_type='ai',
                content=response_data['response'],
                ai_model_used=model_used,
                ai_confidence=response_data.get('confidence', 0.0),
                contains_crisis_keywords=response_data.get('is_crisis', False)
            )
            
            # Update session
            session.updated_at = timezone.now()
            session.save()
            
            # Check for crisis
            if response_data.get('is_crisis', False):
                self._handle_crisis(session, user_message, response_data)
            
            return Response({
                'success': True,
                'user_message': MessageSerializer(user_message).data,
                'ai_response': {
                    'message': response_data['response'],
                    'is_crisis': response_data.get('is_crisis', False),
                    'confidence': response_data.get('confidence', 0.0),
                    'emotion': response_data.get('emotion'),
                    'intensity': response_data.get('intensity', 'medium'),
                    'provider': 'huggingface',
                    'suggested_actions': response_data.get('suggested_actions', [])
                }
            })
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_crisis(self, session, user_message, response_data):
        """Handle crisis detection"""
        try:
            # Update session status
            session.status = 'crisis_escalated'
            session.crisis_level = 10
            session.requires_intervention = True
            session.save()
            
            # Get or create crisis type
            crisis_type, _ = CrisisType.objects.get_or_create(
                name='Suicide/Self-Harm',
                defaults={
                    'description': 'Suicidal ideation or self-harm indicators',
                    'severity_level': 10,
                    'immediate_response': 'Contact emergency services immediately',
                    'escalation_criteria': 'Any mention of suicide or self-harm',
                    'requires_immediate_intervention': True,
                    'auto_escalate': True
                }
            )
            
            # Create crisis alert
            CrisisAlert.objects.create(
                user=session.user,
                crisis_type=crisis_type,
                status='active',
                source='ai_detection',
                severity_level=10,
                confidence_score=1.0,
                description=f"Crisis detected in chat: {user_message.content[:200]}",
                detected_keywords=response_data.get('detected_keywords', []),
                chat_session=session,
                message=user_message,
                follow_up_required=True
            )
            
            logger.warning(f"🚨 Crisis alert created for user {session.user.id}")
            
        except Exception as e:
            logger.error(f"Error handling crisis: {e}")


class ChatSessionListView(APIView):
    """List user's chat sessions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get all chat sessions for user"""
        try:
            sessions = ChatSession.objects.filter(
                user=request.user
            ).order_by('-updated_at')[:20]
            
            serializer = ChatSessionDetailSerializer(sessions, many=True)
            
            return Response({
                'success': True,
                'sessions': serializer.data
            })
        except Exception as e:
            logger.error(f"Error fetching sessions: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatSessionDetailView(APIView):
    """Get chat session details with messages"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, session_id):
        """Get session with all messages"""
        try:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
            
            messages = Message.objects.filter(session=session).order_by('timestamp')
            
            return Response({
                'success': True,
                'session': ChatSessionDetailSerializer(session).data,
                'messages': MessageSerializer(messages, many=True).data
            })
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatSessionEndView(APIView):
    """End a chat session"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, session_id):
        """End chat session"""
        try:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
            
            session.status = 'ended'
            session.ended_at = timezone.now()
            session.save()
            
            return Response({
                'success': True,
                'message': 'Chat session ended'
            })
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
