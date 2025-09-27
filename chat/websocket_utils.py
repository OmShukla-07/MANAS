"""
Utility functions for WebSocket notifications and real-time features.
Provides helper functions to send notifications, alerts, and updates via WebSocket.
"""

import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone


class WebSocketNotifier:
    """
    Utility class for sending WebSocket notifications.
    Provides methods to send various types of real-time updates.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_notification(self, user_id, notification_type, data):
        """
        Send notification to specific user via WebSocket.
        
        Args:
            user_id (int): Target user ID
            notification_type (str): Type of notification
            data (dict): Notification data
        """
        if not self.channel_layer:
            return False
        
        group_name = f'notifications_{user_id}'
        
        async_to_sync(self.channel_layer.group_send)(
            group_name,
            {
                'type': 'notification_message',
                'notification': {
                    'type': notification_type,
                    'data': data,
                    'timestamp': timezone.now().isoformat(),
                }
            }
        )
        return True
    
    def send_chat_message(self, session_id, message_data):
        """
        Send chat message to session participants via WebSocket.
        
        Args:
            session_id (str): Chat session ID
            message_data (dict): Message data
        """
        if not self.channel_layer:
            return False
        
        group_name = f'chat_{session_id}'
        
        async_to_sync(self.channel_layer.group_send)(
            group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )
        return True
    
    def send_crisis_alert(self, alert_data):
        """
        Send crisis alert to all monitoring counselors/admins via WebSocket.
        
        Args:
            alert_data (dict): Crisis alert data
        """
        if not self.channel_layer:
            return False
        
        async_to_sync(self.channel_layer.group_send)(
            'crisis_alerts',
            {
                'type': 'crisis_alert',
                'alert': alert_data
            }
        )
        return True
    
    def send_appointment_reminder(self, user_id, appointment_data):
        """
        Send appointment reminder to user via WebSocket.
        
        Args:
            user_id (int): Target user ID
            appointment_data (dict): Appointment data
        """
        if not self.channel_layer:
            return False
        
        group_name = f'notifications_{user_id}'
        
        async_to_sync(self.channel_layer.group_send)(
            group_name,
            {
                'type': 'appointment_reminder',
                'reminder': appointment_data
            }
        )
        return True
    
    def send_admin_update(self, update_type, data):
        """
        Send admin dashboard update via WebSocket.
        
        Args:
            update_type (str): Type of update
            data (dict): Update data
        """
        if not self.channel_layer:
            return False
        
        async_to_sync(self.channel_layer.group_send)(
            'admin_monitoring',
            {
                'type': 'dashboard_update',
                'data': {
                    'update_type': update_type,
                    'data': data,
                    'timestamp': timezone.now().isoformat(),
                }
            }
        )
        return True
    
    def send_system_alert(self, alert_level, message, details=None):
        """
        Send system alert to administrators via WebSocket.
        
        Args:
            alert_level (str): Alert level (info, warning, error, critical)
            message (str): Alert message
            details (dict): Additional alert details
        """
        if not self.channel_layer:
            return False
        
        async_to_sync(self.channel_layer.group_send)(
            'admin_monitoring',
            {
                'type': 'system_alert',
                'alert': {
                    'level': alert_level,
                    'message': message,
                    'details': details or {},
                    'timestamp': timezone.now().isoformat(),
                }
            }
        )
        return True


# Global notifier instance
notifier = WebSocketNotifier()


def send_real_time_notification(user_id, notification_type, title, message, data=None):
    """
    Send real-time notification to user.
    
    Args:
        user_id (int): Target user ID
        notification_type (str): Type of notification
        title (str): Notification title
        message (str): Notification message
        data (dict): Additional notification data
    """
    notification_data = {
        'title': title,
        'message': message,
        'data': data or {},
    }
    
    return notifier.send_notification(user_id, notification_type, notification_data)


def send_chat_notification(session_id, sender_name, message_preview):
    """
    Send chat notification for new messages.
    
    Args:
        session_id (str): Chat session ID
        sender_name (str): Message sender name
        message_preview (str): Preview of the message
    """
    message_data = {
        'sender_name': sender_name,
        'preview': message_preview[:100],  # Limit preview length
        'timestamp': timezone.now().isoformat(),
    }
    
    return notifier.send_chat_message(session_id, message_data)


def send_crisis_notification(user, crisis_level, description, detected_via='manual'):
    """
    Send crisis alert notification to monitoring staff.
    
    Args:
        user: User object who triggered the crisis alert
        crisis_level (int): Crisis severity level (1-10)
        description (str): Crisis description
        detected_via (str): How the crisis was detected
    """
    alert_data = {
        'user_id': user.id,
        'user_name': f"{user.first_name} {user.last_name}",
        'user_email': user.email,
        'crisis_level': crisis_level,
        'description': description,
        'detected_via': detected_via,
        'timestamp': timezone.now().isoformat(),
        'requires_immediate_attention': crisis_level >= 8,
    }
    
    return notifier.send_crisis_alert(alert_data)


def send_appointment_notification(user_id, appointment, notification_type='reminder'):
    """
    Send appointment-related notification.
    
    Args:
        user_id (int): Target user ID
        appointment: Appointment object
        notification_type (str): Type of notification (reminder, confirmation, cancellation)
    """
    appointment_data = {
        'appointment_id': appointment.id,
        'type': notification_type,
        'date': appointment.date.isoformat(),
        'time': appointment.time.strftime('%H:%M'),
        'counselor_name': f"{appointment.counselor.first_name} {appointment.counselor.last_name}",
        'duration': appointment.duration_minutes,
        'notes': appointment.notes or '',
    }
    
    return notifier.send_appointment_reminder(user_id, appointment_data)


def send_wellness_update(user_id, metric_type, value, trend='stable'):
    """
    Send wellness tracking update notification.
    
    Args:
        user_id (int): Target user ID
        metric_type (str): Type of wellness metric
        value: Current value
        trend (str): Trend direction (improving, stable, declining)
    """
    notification_data = {
        'metric_type': metric_type,
        'value': value,
        'trend': trend,
        'timestamp': timezone.now().isoformat(),
    }
    
    return send_real_time_notification(
        user_id,
        'wellness_update',
        f'{metric_type.title()} Update',
        f'Your {metric_type} has been updated.',
        notification_data
    )


def send_assessment_completion(user_id, assessment_name, score, recommendations):
    """
    Send assessment completion notification.
    
    Args:
        user_id (int): Target user ID
        assessment_name (str): Name of completed assessment
        score: Assessment score
        recommendations (list): List of recommendations
    """
    notification_data = {
        'assessment_name': assessment_name,
        'score': score,
        'recommendations': recommendations,
    }
    
    return send_real_time_notification(
        user_id,
        'assessment_complete',
        'Assessment Completed',
        f'Your {assessment_name} assessment has been completed.',
        notification_data
    )


def send_community_notification(user_id, activity_type, content, community_name):
    """
    Send community activity notification.
    
    Args:
        user_id (int): Target user ID
        activity_type (str): Type of activity (new_post, comment, like, etc.)
        content (str): Activity content
        community_name (str): Name of the community
    """
    notification_data = {
        'activity_type': activity_type,
        'content': content,
        'community_name': community_name,
    }
    
    return send_real_time_notification(
        user_id,
        'community_activity',
        f'New Activity in {community_name}',
        content,
        notification_data
    )


def send_system_maintenance_alert(message, start_time, estimated_duration):
    """
    Send system maintenance alert to all administrators.
    
    Args:
        message (str): Maintenance message
        start_time (datetime): Maintenance start time
        estimated_duration (int): Estimated duration in minutes
    """
    details = {
        'start_time': start_time.isoformat(),
        'estimated_duration': estimated_duration,
        'affected_services': ['chat', 'appointments', 'assessments'],
    }
    
    return notifier.send_system_alert(
        'warning',
        f'Scheduled Maintenance: {message}',
        details
    )


def broadcast_emergency_alert(alert_level, message, affected_users=None):
    """
    Broadcast emergency alert to specified users or all users.
    
    Args:
        alert_level (str): Alert level (info, warning, error, critical)
        message (str): Alert message
        affected_users (list): List of user IDs to notify (None for all)
    """
    if affected_users:
        # Send to specific users
        for user_id in affected_users:
            send_real_time_notification(
                user_id,
                'emergency_alert',
                f'{alert_level.upper()} Alert',
                message
            )
    else:
        # Send to admin monitoring for system-wide broadcast
        notifier.send_system_alert(alert_level, message, {
            'broadcast': True,
            'requires_action': alert_level in ['error', 'critical']
        })
    
    return True