"""
Crisis Alert API Views
Handles crisis detection alerts from frontend
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from chat.models import ChatSession, Message
from crisis.models import CrisisAlert, CrisisType
from .crisis_detection import CrisisDetectionService
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crisis_alert_api(request):
    """
    API endpoint for creating crisis alerts
    Called from frontend when crisis keywords detected
    """
    try:
        user = request.user
        message_text = request.data.get('message', '')
        severity = request.data.get('severity', 'moderate')
        crisis_level = request.data.get('crisis_level', 6)
        client_detected = request.data.get('client_detected', False)
        
        if not message_text:
            return Response(
                {'error': 'Message text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create active session for this user
        session = ChatSession.objects.filter(
            user=user,
            status='active'
        ).first()
        
        if not session:
            # Create a new session if none exists
            session = ChatSession.objects.create(
                user=user,
                session_type='ai_chat',
                status='active',
                title="Crisis Alert Session"
            )
        
        # Create a message record
        message = Message.objects.create(
            session=session,
            sender=user,
            content=message_text,
            message_type='user',
            status='sent'
        )
        
        # Detect crisis (double-check with backend detection)
        detection_result = CrisisDetectionService.detect_crisis(message_text)
        
        # Use the higher severity/level between client and server detection
        if detection_result and detection_result['is_crisis']:
            final_severity = severity if severity == 'severe' else detection_result['severity']
            final_level = max(crisis_level, detection_result['crisis_level'])
            keywords = detection_result['keywords_detected']
        else:
            final_severity = severity
            final_level = crisis_level
            keywords = []
        
        # Create crisis alert using existing CrisisDetectionService
        alert = CrisisDetectionService.create_crisis_alert(user, session, message, {
            'crisis_level': final_level,
            'severity': final_severity,
            'keywords_detected': keywords,
            'requires_immediate_intervention': (final_severity == 'severe'),
            'is_crisis': True
        })
        
        if not alert:
            return Response(
                {'error': 'Failed to create crisis alert'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        logger.warning(
            f"Crisis alert created - User: {user.username}, "
            f"Severity: {final_severity}, Level: {final_level}"
        )
        
        return Response({
            'success': True,
            'alert_id': str(alert.id),
            'severity': final_severity,
            'crisis_level': final_level,
            'helplines': CrisisDetectionService.get_helpline_numbers(),
            'message': 'Crisis alert created successfully. Help is on the way.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating crisis alert: {str(e)}")
        return Response(
            {'error': 'Failed to create crisis alert'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crisis_helplines(request):
    """
    Get crisis helpline numbers
    """
    helplines = CrisisDetectionService.get_helpline_numbers()
    return Response(helplines)
