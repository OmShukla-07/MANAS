"""
AI Chatbot API Views for MANAS Platform
Handles REST API endpoints for AI chatbot interactions
"""

import json
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async
from django.core.cache import cache

from .models import ChatSession, Message, AIPersonality, ChatAnalytics
from .serializers import (
    MessageSerializer, ChatSessionDetailSerializer,
    ChatbotListSerializer, ChatbotStartSessionSerializer
)
from .ai_service import gemini_service
from .manas_ai_service import manas_ai_service
from .enhanced_ai_service import enhanced_manas_ai_service
from crisis.models import CrisisAlert

import logging
logger = logging.getLogger(__name__)


class ChatbotListView(APIView):
    """List available AI chatbot personalities - MANAS companions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get list of available MANAS AI companions with provider info"""
        try:
            # Get companions from enhanced service
            companions = enhanced_manas_ai_service.get_available_companions()
            
            # Get provider status
            provider_status = enhanced_manas_ai_service.get_provider_status()
            
            return Response({
                'success': True,
                'companions': companions,
                'providers': enhanced_manas_ai_service.get_available_providers(),
                'provider_status': provider_status,
                'message': 'MANAS AI companions retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error fetching companions: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch available companions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotStartSessionView(APIView):
    """Start a new AI chat session"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Start new AI chat session with MANAS companion"""
        try:
            # Handle both request.data (DRF) and request.POST/JSON
            if hasattr(request, 'data') and request.data:
                data = request.data
            else:
                import json
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except:
                    data = request.POST
            
            companion_name = data.get('companion', 'priya').lower()
            initial_message = data.get('initial_message', '')
            
            # Validate companion name
            if companion_name not in ['arjun', 'priya', 'vikram']:
                companion_name = 'priya'  # Default fallback
            
            companion_info = manas_ai_service.companion_types.get(companion_name)
            
            # Get or create a test user for session
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                test_user = User.objects.get(username='test_user')
            except User.DoesNotExist:
                # Try to create user, but handle email uniqueness
                try:
                    test_user = User.objects.create_user(
                        username='test_user',
                        email='test@example.com',
                        first_name='Test',
                        last_name='User'
                    )
                except Exception as e:
                    # If email already exists, find and update the existing user
                    try:
                        existing_user = User.objects.get(email='test@example.com')
                        existing_user.username = 'test_user'
                        existing_user.save()
                        test_user = existing_user
                    except:
                        # Last resort: create user with unique email
                        import uuid
                        test_user = User.objects.create_user(
                            username='test_user',
                            email=f'test_{uuid.uuid4().hex[:8]}@example.com',
                            first_name='Test',
                            last_name='User'
                        )
            
            # End any active sessions for test user
            ChatSession.objects.filter(
                user=test_user,
                session_type='ai_chat',
                status='active'
            ).update(status='paused')
            
            # Create chat session
            with transaction.atomic():
                session = ChatSession.objects.create(
                    user=test_user,
                    session_type='ai_chat',
                    status='active',
                    title=f"Chat with {companion_info['name']} {companion_info['emoji']}"
                )
                
                # Create initial user message if provided
                if initial_message:
                    Message.objects.create(
                        session=session,
                        sender=test_user,
                        content=initial_message,
                        message_type='user',
                        status='sent'
                    )
                
                # Generate welcome message
                welcome_messages = {
                    'arjun': f"Hi there 🧘‍♂️ I'm Arjun, your mindfulness and emotional support companion. I'm here to listen with empathy and help you process your feelings. This is a safe space where you can share whatever is on your mind. How are you feeling today?",
                    'priya': f"Hello! 🤗 I'm Priya, and I'm here to provide you with caring support and understanding. I believe in the power of connection and empathy to help you through any challenges you're facing. What would you like to talk about today?",
                    'vikram': f"Hey there! 💪 I'm Vikram, your practical guide for mental wellness and personal growth. I'm here to help you develop strategies, set goals, and build resilience. What challenge can we tackle together today?"
                }
                
                welcome_content = welcome_messages.get(companion_name, welcome_messages['priya'])
                
                # Create welcome message (AI message - use test_user as sender for now)
                Message.objects.create(
                    session=session,
                    sender=test_user,  # Using test_user since sender is required
                    content=welcome_content,
                    message_type='ai',
                    status='sent',
                    ai_model_used='manas_companion',
                    ai_confidence=1.0
                )
            
            return Response({
                'success': True,
                'session': {
                    'id': session.id,
                    'title': session.title,
                    'companion': {
                        'name': companion_info['name'],
                        'emoji': companion_info['emoji'],
                        'color': companion_info['color'],
                        'personality': companion_info['personality']
                    },
                    'created_at': session.created_at.isoformat(),
                    'status': session.status
                },
                'welcome_message': {
                    'content': welcome_content,
                    'companion_name': companion_info['name'],
                    'companion_emoji': companion_info['emoji']
                },
                'message': 'MANAS AI chat session started successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error starting MANAS AI chat session: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to start AI chat session'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_manas_welcome_message(self, companion_name: str, user_name: str) -> str:
        """Generate personalized welcome message for MANAS companions"""
        welcome_messages = {
            'arjun': f"Namaste {user_name}! 🧘‍♂️ I'm Arjun, your mindfulness and emotional support companion. I'm here to listen with empathy and help you process your feelings. This is a safe space where you can share whatever is on your mind. How are you feeling today?",
            'priya': f"Hi {user_name} 🤗 I'm Priya, and I'm here to listen with care and understanding. This is your safe space to share whatever you're feeling or thinking about - there's no judgment here, only support. What's on your heart today?",
            'vikram': f"Hello {user_name}! 💪 I'm Vikram, your practical AI advisor. I specialize in helping you break down challenges into manageable steps and develop concrete strategies for moving forward. What situation would you like to work through together today?"
        }
        return welcome_messages.get(companion_name, f"Hello {user_name}! I'm here to support you. What would you like to talk about?")


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_ai_message(request, session_id):
    """Send message to MANAS AI companion and get response"""
    try:
        # Get session and validate access (temporarily allow any user)
        session = get_object_or_404(
            ChatSession, 
            id=session_id,
            session_type='ai_chat'
        )
        
        if session.status != 'active':
            return Response({
                'success': False,
                'error': 'Chat session is not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle both request.data (DRF) and request.POST/JSON
        if hasattr(request, 'data') and request.data:
            data = request.data
        else:
            import json
            try:
                data = json.loads(request.body.decode('utf-8'))
            except:
                data = request.POST
        
        message_content = data.get('message', '').strip()
        # Extract companion from session title or default to priya
        companion_name = 'priya'
        if 'Arjun' in session.title:
            companion_name = 'arjun'
        elif 'Vikram' in session.title:
            companion_name = 'vikram'
        
        if not message_content:
            return Response({
                'success': False,
                'error': 'Message content is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user message
        with transaction.atomic():
            # Get or create a test user for messaging
            from django.contrib.auth import get_user_model
            User = get_user_model()
            test_user = User.objects.first()
            
            user_message = Message.objects.create(
                session=session,
                sender=test_user,
                content=message_content,
                message_type='user',
                status='sent'
            )
            
            # Get conversation history for context
            conversation_history = []
            recent_messages = session.messages.order_by('-created_at')[:10]
            for msg in reversed(recent_messages):
                conversation_history.append({
                    'content': msg.content,
                    'sender_type': 'user' if msg.sender else 'ai',
                    'timestamp': msg.created_at.isoformat()
                })
            
            # Generate MANAS AI response using enhanced service
            ai_response = enhanced_manas_ai_service.generate_response_sync(
                message=message_content,
                companion_type=companion_name,
                session_context=None,  # We'll build context from conversation_history
                provider=data.get('provider')  # Allow provider selection
            )
            
            # Create AI response message
            ai_message = Message.objects.create(
                session=session,
                sender=test_user,  # Required field
                content=ai_response['content'] if isinstance(ai_response, dict) else ai_response,
                message_type='ai',
                ai_model_used=ai_response.get('model', 'unknown') if isinstance(ai_response, dict) else 'gemini-2.5-flash',
                status='sent',
                contains_crisis_keywords=False  # We'll implement crisis detection later
            )
            
        # Update session with crisis analysis if needed (placeholder for now)
        crisis_detected = False  # We'll implement proper crisis detection later
        if crisis_detected:
            session.crisis_level = max(session.crisis_level, 5)
            session.requires_intervention = True
            session.save()
            
            # Create crisis alert if intervention required
            CrisisAlert.objects.get_or_create(
                user=test_user,
                session=session,
                defaults={
                    'alert_type': 'ai_detected',
                    'severity': 'high',
                    'description': f"MANAS AI detected crisis indicators in conversation",
                    'metadata': {
                        'companion': companion_name,
                        'crisis_keywords': [],
                        'message_id': str(ai_message.id)
                    }
                }
            )        # Update session timestamp
        session.updated_at = timezone.now()
        session.save()
        
        # Get companion info for response
        companion_info = manas_ai_service.companion_types.get(companion_name)
        
        response_data = {
            'success': True,
            'user_message': {
                'id': str(user_message.id),
                'content': message_content,
                'timestamp': user_message.created_at.isoformat(),
                'sender': 'user'
            },
            'ai_response': {
                'id': str(ai_message.id),
                'content': ai_response['content'] if isinstance(ai_response, dict) else ai_response,
                'timestamp': ai_message.created_at.isoformat(),
                'sender': 'ai',
                'companion_name': companion_info['name'],
                'companion_emoji': companion_info['emoji'],
                'companion_color': companion_info['color'],
                'model_used': ai_response.get('model', 'gemini-2.5-flash') if isinstance(ai_response, dict) else 'gemini-2.5-flash',
                'provider': ai_response.get('provider_name', 'Google Gemini') if isinstance(ai_response, dict) else 'Google Gemini'
            },
            'session_id': str(session.id),
            'crisis_detected': crisis_detected
        }
        
        # Add crisis support info if needed
        if crisis_detected:
            response_data['crisis_support'] = {
                'message': 'Crisis indicators detected. Professional support is recommended.',
                'hotlines': [
                    {'name': 'National Suicide Prevention Lifeline', 'number': '988'},
                    {'name': 'Crisis Text Line', 'number': '741741', 'text': 'Text HOME'},
                    {'name': 'MANAS Counselor Support', 'action': 'schedule_appointment'},
                    {'name': 'Emergency Services', 'number': '911'}
                ]
            }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing MANAS AI message: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to process message'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def end_ai_session(request, session_id):
    """End AI chat session and generate summary"""
    try:
        session = get_object_or_404(
            ChatSession,
            id=session_id,
            user=request.user,
            session_type=ChatSession.SessionType.AI_CHAT
        )
        
        if session.status != ChatSession.SessionStatus.ACTIVE:
            return Response({
                'success': False,
                'error': 'Session is not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # End session
        session.status = ChatSession.SessionStatus.ENDED
        session.ended_at = timezone.now()
        
        # Generate session summary
        session.session_summary = gemini_service.generate_session_summary_sync(session)
        session.save()
        
        # Create analytics
        messages = session.messages.all()
        analytics, created = ChatAnalytics.objects.get_or_create(
            session=session,
            defaults={
                'total_messages': messages.count(),
                'user_message_count': messages.filter(message_type=Message.MessageType.USER).count(),
                'ai_response_count': messages.filter(message_type=Message.MessageType.AI).count(),
                'highest_crisis_level': session.crisis_level,
                'intervention_triggered': session.requires_intervention,
                'ai_summary': session.session_summary
            }
        )
        
        return Response({
            'success': True,
            'message': 'Session ended successfully',
            'session_summary': session.session_summary,
            'session_stats': {
                'duration_minutes': int((session.ended_at - session.started_at).total_seconds() / 60),
                'total_messages': analytics.total_messages,
                'crisis_level': session.crisis_level,
                'intervention_required': session.requires_intervention
            }
        })
        
    except Exception as e:
        logger.error(f"Error ending AI session: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to end session'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_ai_sessions(request):
    """Get user's MANAS AI chat sessions with pagination"""
    try:
        sessions = ChatSession.objects.filter(
            user=request.user,
            session_type='ai_chat'
        ).order_by('-updated_at')
        
        # Pagination
        page_size = int(request.GET.get('page_size', 10))
        page = int(request.GET.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_sessions = sessions.count()
        paginated_sessions = sessions[start:end]
        
        session_data = []
        for session in paginated_sessions:
            # Extract companion type from session title
            companion_type = 'priya'  # default
            if 'Arjun' in session.title:
                companion_type = 'arjun'
            elif 'Vikram' in session.title:
                companion_type = 'vikram'
            
            companion_info = manas_ai_service.companion_types.get(
                companion_type,
                manas_ai_service.companion_types['priya']
            )
            
            # Get last message preview
            last_message = session.messages.order_by('-created_at').first()
            last_message_preview = ""
            if last_message:
                last_message_preview = last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content
            
            session_data.append({
                'id': str(session.id),
                'title': session.title,
                'companion': {
                    'name': companion_info['name'],
                    'emoji': companion_info['emoji'],
                    'color': companion_info['color']
                },
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'status': session.status,
                'message_count': session.messages.count(),
                'last_message_preview': last_message_preview
            })
        
        return Response({
            'success': True,
            'sessions': session_data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_sessions': total_sessions,
                'total_pages': (total_sessions + page_size - 1) // page_size
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching user MANAS AI sessions: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch sessions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_chat_history(request, session_id):
    """Get chat history for a MANAS AI session"""
    try:
        session = get_object_or_404(
            ChatSession,
            id=session_id,
            user=request.user,
            session_type='ai_chat'
        )
        
        messages = session.messages.order_by('created_at')
        message_data = []
        
        for msg in messages:
            message_data.append({
                'id': str(msg.id),
                'content': msg.content,
                'sender': 'user' if msg.sender else 'ai',
                'timestamp': msg.created_at.isoformat(),
                'message_type': msg.message_type
            })
        
        # Extract companion type from session title
        companion_type = 'priya'  # default
        if 'Arjun' in session.title:
            companion_type = 'arjun'
        elif 'Vikram' in session.title:
            companion_type = 'vikram'
            
        companion_info = manas_ai_service.companion_types.get(
            companion_type, 
            manas_ai_service.companion_types['priya']
        )
        
        return Response({
            'success': True,
            'session': {
                'id': str(session.id),
                'title': session.title,
                'companion': {
                    'name': companion_info['name'],
                    'emoji': companion_info['emoji'],
                    'color': companion_info['color']
                },
                'created_at': session.created_at.isoformat(),
                'status': session.status
            },
            'messages': message_data
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get chat history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def manas_chat_quick_start(request):
    """Quick start a MANAS AI chat with default companion and message"""
    try:
        companion_name = request.data.get('companion', 'priya').lower()
        message = request.data.get('message', '').strip()
        
        if companion_name not in ['arjun', 'priya', 'vikram']:
            companion_name = 'priya'
        
        # Start new session
        start_session_data = {'companion': companion_name}
        if message:
            start_session_data['initial_message'] = message
        
        # Create mock request for session start
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.user = request.user
        mock_request.data = start_session_data
        
        view = ChatbotStartSessionView()
        session_response = view.post(mock_request)
        
        if session_response.status_code != 201:
            return Response({
                'success': False,
                'error': 'Failed to start session'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        session_data = session_response.data
        
        # If there's an initial message, send it
        if message:
            mock_request.data = {'message': message}
            message_response = send_ai_message(mock_request, session_data['session']['id'])
            
            if message_response.status_code == 201:
                return Response({
                    'success': True,
                    'session': session_data['session'],
                    'messages': [
                        session_data['welcome_message'],
                        message_response.data['user_message'],
                        message_response.data['ai_response']
                    ]
                })
        
        return Response({
            'success': True,
            'session': session_data['session'],
            'welcome_message': session_data['welcome_message']
        })
        
    except Exception as e:
        logger.error(f"Error in MANAS quick start: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to quick start chat'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ai_providers(request):
    """Get available AI providers and their status"""
    try:
        providers = enhanced_manas_ai_service.get_available_providers()
        provider_status = enhanced_manas_ai_service.get_provider_status()
        
        return Response({
            'success': True,
            'providers': providers,
            'provider_status': provider_status,
            'default_provider': enhanced_manas_ai_service.default_provider
        })
    except Exception as e:
        logger.error(f"Error getting AI providers: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get AI providers'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)