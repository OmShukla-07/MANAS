from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    ChatSession, Message, AIPersonality, MessageReaction,
    ChatTemplate, ChatAnalytics
)
from .serializers import (
    ChatSessionListSerializer, ChatSessionDetailSerializer,
    MessageSerializer, MessageCreateSerializer, MessageReactionSerializer,
    AIPersonalitySerializer, ChatTemplateSerializer, ChatAnalyticsSerializer,
    SessionStartSerializer, SessionFeedbackSerializer, CrisisDetectionSerializer,
    ChatStatsSerializer
)
from .websocket_utils import (
    send_chat_notification,
    send_crisis_notification,
    send_real_time_notification
)

User = get_user_model()


class ChatSessionListView(generics.ListAPIView):
    """List all chat sessions for the authenticated user"""
    serializer_class = ChatSessionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = ChatSession.objects.filter(user=user).order_by('-updated_at')
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by session type if provided
        session_type = self.request.query_params.get('type')
        if session_type:
            queryset = queryset.filter(session_type=session_type)
        
        return queryset


class ChatSessionCreateView(generics.CreateAPIView):
    """Create a new chat session"""
    serializer_class = SessionStartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the chat session
        session_data = {
            'user': request.user,
            'session_type': serializer.validated_data['session_type'],
            'title': serializer.validated_data.get('title', f"Chat Session - {timezone.now().strftime('%Y-%m-%d %H:%M')}"),
            'status': 'active'
        }
        
        # Set AI personality if provided
        ai_personality_id = serializer.validated_data.get('ai_personality_id')
        if ai_personality_id:
            session_data['ai_personality'] = AIPersonality.objects.get(id=ai_personality_id)
        else:
            # Use default AI personality
            default_personality = AIPersonality.objects.filter(is_default=True, is_active=True).first()
            if default_personality:
                session_data['ai_personality'] = default_personality
        
        session = ChatSession.objects.create(**session_data)
        
        # Send initial message if provided
        initial_message = serializer.validated_data.get('initial_message')
        if initial_message:
            Message.objects.create(
                session=session,
                sender=request.user,
                content=initial_message,
                message_type='text'
            )
            
            # Trigger AI response (this would be handled by the AI service)
            # For now, we'll create a placeholder response
            ai_response = self.generate_ai_response(session, initial_message)
            Message.objects.create(
                session=session,
                content=ai_response,
                message_type='text',
                status='sent'
            )
        
        return Response(
            ChatSessionDetailSerializer(session).data,
            status=status.HTTP_201_CREATED
        )
    
    def generate_ai_response(self, session, user_message):
        """Generate AI response (placeholder - will be replaced with actual AI integration)"""
        personality = session.ai_personality
        if personality and personality.greeting_message:
            return personality.greeting_message
        
        return "Hello! I'm MANAS AI, your mental health companion. I'm here to listen and support you. How are you feeling today?"


class ChatSessionDetailView(generics.RetrieveUpdateAPIView):
    """Get and update chat session details"""
    serializer_class = ChatSessionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class MessageListView(generics.ListAPIView):
    """List messages in a chat session"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(ChatSession, id=session_id, user=self.request.user)
        
        # Mark messages as read
        session.messages.filter(is_read=False).exclude(sender=self.request.user).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return session.messages.all().order_by('created_at')


class MessageCreateView(generics.CreateAPIView):
    """Send a new message in a chat session"""
    serializer_class = MessageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        
        # Add session to the request data
        request.data['session'] = session.id
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        
        # Update session timestamp
        session.updated_at = timezone.now()
        session.save()
        
        # Check for crisis keywords
        crisis_detected = self.contains_crisis_keywords(message.content)
        if crisis_detected:
            message.contains_crisis_keywords = True
            message.crisis_keywords_detected = ['crisis', 'suicide', 'harm']  # Placeholder
            message.save()
            
            # Update session crisis level if needed
            if session.crisis_level == 0:
                session.crisis_level = 3  # Low-medium crisis level
                session.save()
            
            # Send crisis alert via WebSocket
            send_crisis_notification(
                request.user,
                session.crisis_level,
                f"Crisis keywords detected in chat: {message.content[:100]}...",
                'chat'
            )
        
        # Send real-time chat notification via WebSocket
        send_chat_notification(
            session.id,
            f"{request.user.first_name} {request.user.last_name}",
            message.content
        )
        
        # Notify other participants in the chat (if counselor session)
        if session.session_type == 'counselor' and session.counselor:
            send_real_time_notification(
                session.counselor.id,
                'new_message',
                'New Message',
                f'You have a new message from {request.user.first_name}',
                {
                    'session_id': session.id,
                    'message_preview': message.content[:50],
                    'sender_name': f"{request.user.first_name} {request.user.last_name}"
                }
            )
        
        # Trigger AI response for AI sessions
        if session.session_type == 'ai_chat':
            ai_response = self.generate_ai_response(session, message.content, crisis_detected)
            ai_message = Message.objects.create(
                session=session,
                content=ai_response,
                message_type='text',
                status='sent'
            )
            
            # Send AI response notification via WebSocket
            send_real_time_notification(
                request.user.id,
                'ai_response',
                'MANAS AI Response',
                'MANAS AI has responded to your message',
                {
                    'session_id': session.id,
                    'message_id': ai_message.id,
                    'content': ai_response
                }
            )
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )
    
    def contains_crisis_keywords(self, content):
        """Check if message contains crisis keywords (placeholder)"""
        crisis_keywords = ['suicide', 'kill myself', 'end it all', 'crisis', 'emergency']
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in crisis_keywords)
    
    def generate_ai_response(self, session, user_message, crisis_detected=False):
        """Generate AI response (placeholder)"""
        # This is a simplified response generator
        # In production, this would call the actual AI service
        
        if crisis_detected:
            return "I'm concerned about what you've shared. It sounds like you're going through a really difficult time. Please remember that you're not alone, and there are people who want to help. Would you like me to connect you with a crisis counselor?"
        
        # Basic responses based on common patterns
        user_message_lower = user_message.lower()
        
        if any(word in user_message_lower for word in ['sad', 'depressed', 'down']):
            return "I hear that you're feeling down. It's okay to feel sad sometimes - your feelings are valid. Would you like to talk about what's been weighing on your mind?"
        
        if any(word in user_message_lower for word in ['anxious', 'worried', 'nervous']):
            return "It sounds like you're experiencing some anxiety. That can be really overwhelming. Let's try to work through this together. Can you tell me what's making you feel worried?"
        
        if any(word in user_message_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! It's good to see you here. I'm here to listen and support you. How are you feeling today?"
        
        return "I'm here to listen and support you. Can you tell me more about how you're feeling or what's on your mind?"


class MessageReactionCreateView(generics.CreateAPIView):
    """Add reaction to a message"""
    serializer_class = MessageReactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        message_id = kwargs.get('message_id')
        message = get_object_or_404(Message, id=message_id)
        
        # Check if user has access to this message
        if message.session.user != request.user:
            return Response(
                {'error': 'You do not have permission to react to this message'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove existing reaction if any
        MessageReaction.objects.filter(user=request.user, message=message).delete()
        
        # Create new reaction
        reaction = MessageReaction.objects.create(
            user=request.user,
            message=message,
            reaction_type=request.data.get('reaction_type')
        )
        
        return Response(
            MessageReactionSerializer(reaction).data,
            status=status.HTTP_201_CREATED
        )


class SessionFeedbackView(APIView):
    """Submit feedback for a chat session"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        
        serializer = SessionFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session.feedback_rating = serializer.validated_data['rating']
        session.feedback_comment = serializer.validated_data.get('comment', '')
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.save()
        
        # Create analytics record
        self.create_session_analytics(session)
        
        return Response({'message': 'Feedback submitted successfully'})
    
    def create_session_analytics(self, session):
        """Create analytics record for the session"""
        messages = session.messages.all()
        
        ChatAnalytics.objects.create(
            session=session,
            total_messages=messages.count(),
            user_messages=messages.filter(sender=session.user).count(),
            ai_messages=messages.filter(sender__isnull=True).count(),
            counselor_messages=messages.filter(sender__role='counselor').count(),
            session_duration_minutes=self.calculate_session_duration(session),
            crisis_detected=session.crisis_level > 0,
            crisis_level=session.crisis_level,
            user_satisfaction=session.feedback_rating,
            resolution_status='completed' if session.status == 'completed' else 'ongoing'
        )
    
    def calculate_session_duration(self, session):
        """Calculate session duration in minutes"""
        if session.ended_at:
            duration = session.ended_at - session.created_at
            return int(duration.total_seconds() / 60)
        return 0


class AIPersonalityListView(generics.ListAPIView):
    """List available AI personalities"""
    serializer_class = AIPersonalitySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AIPersonality.objects.filter(is_active=True)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_stats(request):
    """Get chat statistics for the user"""
    user = request.user
    
    sessions = ChatSession.objects.filter(user=user)
    messages = Message.objects.filter(session__user=user)
    
    stats = {
        'total_sessions': sessions.count(),
        'active_sessions': sessions.filter(status='active').count(),
        'completed_sessions': sessions.filter(status='completed').count(),
        'crisis_sessions': sessions.filter(crisis_level__gt=0).count(),
        'average_session_duration': 0,
        'total_messages': messages.count(),
        'user_satisfaction_average': 0,
        'most_discussed_topics': []
    }
    
    # Calculate average session duration
    completed_sessions = sessions.filter(status='completed', ended_at__isnull=False)
    if completed_sessions.exists():
        total_duration = sum([
            (session.ended_at - session.created_at).total_seconds() / 60
            for session in completed_sessions
        ])
        stats['average_session_duration'] = total_duration / completed_sessions.count()
    
    # Calculate average satisfaction
    rated_sessions = sessions.filter(feedback_rating__isnull=False)
    if rated_sessions.exists():
        stats['user_satisfaction_average'] = rated_sessions.aggregate(
            avg_rating=Avg('feedback_rating')
        )['avg_rating']
    
    serializer = ChatStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def end_session(request, session_id):
    """End a chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    if session.status == 'active':
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.save()
        
        return Response({'message': 'Session ended successfully'})
    
    return Response(
        {'error': 'Session is not active'},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_counselor(request, session_id):
    """Request human counselor intervention"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    session.requires_intervention = True
    session.intervention_notes = request.data.get('reason', 'User requested counselor assistance')
    session.save()
    
    # Here you would typically notify available counselors
    # For now, we'll just update the session
    
    return Response({'message': 'Counselor has been notified. They will join the session shortly.'})


# Admin/Counselor views
class AdminChatSessionListView(generics.ListAPIView):
    """Admin view to list all chat sessions"""
    serializer_class = ChatSessionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_admin and not self.request.user.is_counselor:
            return ChatSession.objects.none()
        
        queryset = ChatSession.objects.all().order_by('-created_at')
        
        # Filter crisis sessions if requested
        if self.request.query_params.get('crisis_only') == 'true':
            queryset = queryset.filter(crisis_level__gt=0)
        
        # Filter sessions requiring intervention
        if self.request.query_params.get('intervention_required') == 'true':
            queryset = queryset.filter(requires_intervention=True)
        
        return queryset


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_chat_stats(request):
    """Get chat statistics for admin dashboard"""
    if not request.user.is_admin:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_sessions': ChatSession.objects.count(),
        'active_sessions': ChatSession.objects.filter(status='active').count(),
        'completed_sessions': ChatSession.objects.filter(status='completed').count(),
        'crisis_sessions': ChatSession.objects.filter(crisis_level__gt=0).count(),
        'sessions_today': ChatSession.objects.filter(created_at__date=today).count(),
        'sessions_this_week': ChatSession.objects.filter(created_at__date__gte=week_ago).count(),
        'average_session_duration': 0,
        'total_messages': Message.objects.count(),
        'user_satisfaction_average': 0,
        'intervention_requests': ChatSession.objects.filter(requires_intervention=True).count()
    }
    
    # Calculate averages
    completed_sessions = ChatSession.objects.filter(status='completed', ended_at__isnull=False)
    if completed_sessions.exists():
        analytics = ChatAnalytics.objects.filter(session__in=completed_sessions)
        if analytics.exists():
            stats['average_session_duration'] = analytics.aggregate(
                avg_duration=Avg('session_duration_minutes')
            )['avg_duration'] or 0
            stats['user_satisfaction_average'] = analytics.aggregate(
                avg_satisfaction=Avg('user_satisfaction')
            )['avg_satisfaction'] or 0
    
    return Response(stats)
