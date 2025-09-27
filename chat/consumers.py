"""
WebSocket consumers for real-time functionality in MANAS platform.
Handles chat sessions, notifications, crisis alerts, and admin monitoring.
"""

import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from .models import ChatSession, Message, AIPersonality
from crisis.models import CrisisAlert
from accounts.models import CustomUser
from .realtime_crisis import process_real_time_message
from .ai_service import gemini_service

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat functionality.
    Handles AI and counselor chat sessions with real-time messaging.
    """
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        
        # Get user from scope (JWT authentication)
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Verify user has access to this chat session
        has_access = await self.verify_chat_access()
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send chat history
        await self.send_chat_history()
        
        # Update user status to online
        await self.update_user_status(True)
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update user status to offline
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.update_user_status(False)
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'session_update':
                await self.handle_session_update(data)
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_message(self, data):
        """Handle incoming chat messages"""
        content = data.get('content', '').strip()
        if not content:
            return
        
        # Create message in database
        message = await self.create_message(content)
        if not message:
            await self.send_error("Failed to create message")
            return
        
        # Check for crisis keywords
        crisis_detected = await self.check_crisis_content(content)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.id,
                    'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
                    'sender_role': message.sender.role,
                    'timestamp': message.created_at.isoformat(),
                    'is_ai_response': message.is_ai_response,
                    'crisis_detected': crisis_detected,
                }
            }
        )
        
        # Handle AI response if this is an AI session
        session = await self.get_session()
        if session and session.session_type == 'ai' and not message.is_ai_response:
            await self.generate_ai_response(message, crisis_detected)
    
    async def handle_typing(self, data):
        """Handle typing indicators"""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_name': f"{self.user.first_name} {self.user.last_name}",
                'is_typing': is_typing
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle message read receipts"""
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_read(message_id)
    
    async def handle_session_update(self, data):
        """Handle session status updates"""
        status = data.get('status')
        if status in ['active', 'ended', 'paused']:
            await self.update_session_status(status)
    
    # WebSocket message handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message']
        }, cls=DjangoJSONEncoder))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator back to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'data': {
                    'user_id': event['user_id'],
                    'user_name': event['user_name'],
                    'is_typing': event['is_typing']
                }
            }))
    
    async def crisis_alert(self, event):
        """Send crisis alert to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'crisis_alert',
            'data': event['alert']
        }, cls=DjangoJSONEncoder))
    
    async def ai_response(self, event):
        """Send AI response to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'ai_response',
            'data': event['response']
        }, cls=DjangoJSONEncoder))
    
    # Database operations
    @database_sync_to_async
    def verify_chat_access(self):
        """Verify user has access to this chat session"""
        try:
            session = ChatSession.objects.get(id=self.session_id)
            return (session.user == self.user or 
                   session.counselor == self.user or
                   self.user.role == 'admin')
        except ChatSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_session(self):
        """Get chat session"""
        try:
            return ChatSession.objects.get(id=self.session_id)
        except ChatSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_message(self, content):
        """Create new message in database"""
        try:
            session = ChatSession.objects.get(id=self.session_id)
            message = Message.objects.create(
                session=session,
                sender=self.user,
                content=content,
                is_ai_response=False
            )
            return message
        except Exception:
            return None
    
    @database_sync_to_async
    def send_chat_history(self):
        """Send recent chat history to newly connected user"""
        try:
            session = ChatSession.objects.get(id=self.session_id)
            messages = Message.objects.filter(session=session).order_by('-created_at')[:50]
            
            history = []
            for message in reversed(messages):
                history.append({
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.id,
                    'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
                    'sender_role': message.sender.role,
                    'timestamp': message.created_at.isoformat(),
                    'is_ai_response': message.is_ai_response,
                })
            
            # Send history in a single message
            asyncio.create_task(self.send(text_data=json.dumps({
                'type': 'chat_history',
                'data': {'messages': history}
            }, cls=DjangoJSONEncoder)))
            
        except Exception:
            pass
    
    @database_sync_to_async
    def check_crisis_content(self, content):
        """Check if message content contains crisis keywords"""
        from django.conf import settings
        crisis_keywords = getattr(settings, 'CRISIS_KEYWORDS', [])
        
        content_lower = content.lower()
        for keyword in crisis_keywords:
            if keyword.lower() in content_lower:
                # Create crisis alert
                self.create_crisis_alert(content)
                return True
        return False
    
    @database_sync_to_async
    def create_crisis_alert(self, content):
        """Create crisis alert in database"""
        try:
            session = ChatSession.objects.get(id=self.session_id)
            alert = CrisisAlert.objects.create(
                user=self.user,
                crisis_level=8,  # High severity for detected keywords
                description=f"Crisis keywords detected in chat: {content[:100]}...",
                status='open',
                detected_via='chat'
            )
            
            # Send alert to crisis monitoring channel
            asyncio.create_task(self.notify_crisis_monitors(alert))
            
        except Exception:
            pass
    
    async def notify_crisis_monitors(self, alert):
        """Notify crisis monitoring channels"""
        await self.channel_layer.group_send(
            'crisis_alerts',
            {
                'type': 'crisis_alert',
                'alert': {
                    'id': alert.id,
                    'user_id': alert.user.id,
                    'user_name': f"{alert.user.first_name} {alert.user.last_name}",
                    'crisis_level': alert.crisis_level,
                    'description': alert.description,
                    'timestamp': alert.created_at.isoformat(),
                }
            }
        )
    
    async def generate_ai_response(self, user_message, crisis_detected):
        """Generate AI response using GeminiAI service"""
        try:
            # Get session and determine chatbot type
            session = await self.get_session()
            if not session:
                return
            
            # Default to HYBRID if not specified
            chatbot_type = getattr(session, 'chatbot_type', 'HYBRID')
            
            # Get conversation history
            conversation_history = await self.get_conversation_history(session)
            
            # Generate AI response using our service
            ai_response_data = await gemini_service.generate_response(
                user_message=user_message.content,
                chatbot_type=chatbot_type,
                session=session,
                conversation_history=conversation_history
            )
            
            # Create AI response message
            ai_message = await self.create_ai_message(
                content=ai_response_data['content'],
                model_used=ai_response_data['model_used'],
                confidence=ai_response_data.get('confidence', 0.8),
                crisis_analysis=ai_response_data.get('crisis_analysis', {})
            )
            
            if ai_message:
                # Send AI response to WebSocket
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'ai_response',
                        'response': {
                            'id': str(ai_message.id),
                            'content': ai_message.content,
                            'sender_name': 'MANAS AI Assistant',
                            'sender_role': 'ai',
                            'chatbot_type': chatbot_type,
                            'model_used': ai_response_data['model_used'],
                            'confidence': ai_response_data.get('confidence', 0.8),
                            'timestamp': ai_message.created_at.isoformat(),
                            'crisis_detected': ai_response_data.get('crisis_analysis', {}).get('is_crisis', False),
                            'intervention_required': ai_response_data.get('crisis_analysis', {}).get('requires_intervention', False)
                        }
                    }
                )
                
                # Handle crisis escalation if needed
                crisis_analysis = ai_response_data.get('crisis_analysis', {})
                if crisis_analysis.get('requires_intervention'):
                    await self.handle_crisis_escalation(session, crisis_analysis)
        
        except Exception as e:
            # Fallback to basic response
            await self.send_fallback_response(str(e))
    
    async def send_fallback_response(self, error_msg):
        """Send fallback response when AI fails"""
        fallback_content = "I'm having trouble processing your message right now, but I want you to know that I'm here for you. Could you please try again, or would you like to speak with a human counselor?"
        
        ai_message = await self.create_ai_message(
            content=fallback_content,
            model_used="fallback",
            confidence=0.5
        )
        
        if ai_message:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ai_response',
                    'response': {
                        'id': str(ai_message.id),
                        'content': ai_message.content,
                        'sender_name': 'MANAS AI Assistant',
                        'sender_role': 'ai',
                        'timestamp': ai_message.created_at.isoformat(),
                        'is_fallback': True
                    }
                }
            )
    
    @database_sync_to_async
    def get_conversation_history(self, session):
        """Get conversation history for AI context"""
        try:
            messages = list(
                session.messages.order_by('created_at').values(
                    'content', 'message_type', 'created_at'
                )[-10:]  # Last 10 messages for context
            )
            
            history = []
            for msg in messages:
                history.append({
                    'content': msg['content'],
                    'message_type': msg['message_type'],
                    'created_at': msg['created_at'],
                    'sender_type': 'user' if msg['message_type'] == 'user' else 'ai'
                })
            
            return history
        except Exception:
            return []
    
    async def handle_crisis_escalation(self, session, crisis_analysis):
        """Handle crisis escalation notifications"""
        try:
            # Create crisis alert
            await self.create_crisis_alert(session, crisis_analysis)
            
            # Notify admin/counselor channels
            await self.channel_layer.group_send(
                'crisis_monitoring',
                {
                    'type': 'crisis_alert',
                    'alert': {
                        'session_id': str(session.id),
                        'user_id': str(session.user.id),
                        'user_name': session.user.get_full_name(),
                        'crisis_level': crisis_analysis.get('crisis_score', 0),
                        'keywords': crisis_analysis.get('keywords_detected', []),
                        'timestamp': timezone.now().isoformat(),
                        'requires_immediate_attention': True
                    }
                }
            )
        except Exception as e:
            pass  # Log error but don't break chat flow
    
    @database_sync_to_async
    def create_crisis_alert(self, session, crisis_analysis):
        """Create crisis alert in database"""
        try:
            CrisisAlert.objects.get_or_create(
                user=session.user,
                session=session,
                defaults={
                    'alert_type': CrisisAlert.AlertType.AI_DETECTED,
                    'severity': CrisisAlert.SeverityLevel.HIGH,
                    'description': f"AI detected crisis indicators: {', '.join(crisis_analysis.get('keywords_detected', []))}",
                    'metadata': {
                        'crisis_score': crisis_analysis.get('crisis_score', 0),
                        'detected_keywords': crisis_analysis.get('keywords_detected', []),
                        'ai_confidence': crisis_analysis.get('confidence', 0.0)
                    }
                }
            )
        except Exception:
            pass
    
    @database_sync_to_async
    def create_ai_message(self, content, model_used="gemini-1.5-flash", confidence=0.8, crisis_analysis=None):
        """Create AI response message with enhanced metadata"""
        try:
            session = ChatSession.objects.get(id=self.session_id)
            
            message = Message.objects.create(
                session=session,
                sender=session.user,  # AI messages use session user as sender
                content=content,
                message_type=Message.MessageType.AI,
                ai_model_used=model_used,
                ai_confidence=confidence,
                status=Message.MessageStatus.DELIVERED
            )
            
            # Update crisis-related fields if analysis provided
            if crisis_analysis:
                message.contains_crisis_keywords = crisis_analysis.get('is_crisis', False)
                message.crisis_indicators = crisis_analysis.get('keywords_detected', [])
                message.save()
            
            return message
        except Exception as e:
            return None
    
    @database_sync_to_async
    def update_user_status(self, is_online):
        """Update user online status"""
        try:
            self.user.last_seen = timezone.now()
            if hasattr(self.user, 'is_online'):
                self.user.is_online = is_online
            self.user.save()
        except Exception:
            pass
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(id=message_id)
            # Add read receipt logic here
            pass
        except Exception:
            pass
    
    @database_sync_to_async
    def update_session_status(self, status):
        """Update session status"""
        try:
            session = ChatSession.objects.get(id=self.session_id)
            session.status = status
            if status == 'ended':
                session.ended_at = timezone.now()
            session.save()
        except Exception:
            pass
    
    async def send_error(self, message):
        """Send error message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    Handles appointment reminders, system notifications, and updates.
    """
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated or str(self.user.id) != self.user_id:
            await self.close()
            return
        
        self.room_group_name = f'notifications_{self.user_id}'
        
        # Join notification group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send any pending notifications
        await self.send_pending_notifications()
    
    async def disconnect(self, close_code):
        # Leave notification group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            notification_type = data.get('type')
            
            if notification_type == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            elif notification_type == 'get_unread_count':
                count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': count
                }))
                
        except json.JSONDecodeError:
            pass
    
    # WebSocket message handlers
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['notification']
        }, cls=DjangoJSONEncoder))
    
    async def appointment_reminder(self, event):
        """Send appointment reminder to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'appointment_reminder',
            'data': event['reminder']
        }, cls=DjangoJSONEncoder))
    
    @database_sync_to_async
    def send_pending_notifications(self):
        """Send any pending notifications to user"""
        # Implementation for fetching and sending pending notifications
        pass
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        # Implementation for marking notification as read
        pass
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notification count"""
        # Implementation for getting unread count
        return 0


class CrisisConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for crisis alerts and emergency notifications.
    Used by counselors and admins to monitor crisis situations.
    """
    
    async def connect(self):
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Only counselors and admins can connect to crisis monitoring
        if self.user.role not in ['counselor', 'admin']:
            await self.close()
            return
        
        # Join crisis alerts group
        await self.channel_layer.group_add(
            'crisis_alerts',
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave crisis alerts group
        await self.channel_layer.group_discard(
            'crisis_alerts',
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'acknowledge_alert':
                alert_id = data.get('alert_id')
                await self.acknowledge_crisis_alert(alert_id)
            elif action == 'escalate_alert':
                alert_id = data.get('alert_id')
                await self.escalate_crisis_alert(alert_id)
                
        except json.JSONDecodeError:
            pass
    
    # WebSocket message handlers
    async def crisis_alert(self, event):
        """Send crisis alert to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'crisis_alert',
            'data': event['alert']
        }, cls=DjangoJSONEncoder))
    
    @database_sync_to_async
    def acknowledge_crisis_alert(self, alert_id):
        """Acknowledge crisis alert"""
        try:
            alert = CrisisAlert.objects.get(id=alert_id)
            alert.acknowledged_by = self.user
            alert.acknowledged_at = timezone.now()
            alert.status = 'acknowledged'
            alert.save()
        except CrisisAlert.DoesNotExist:
            pass
    
    @database_sync_to_async
    def escalate_crisis_alert(self, alert_id):
        """Escalate crisis alert"""
        try:
            alert = CrisisAlert.objects.get(id=alert_id)
            alert.crisis_level = min(alert.crisis_level + 2, 10)  # Increase severity
            alert.status = 'escalated'
            alert.save()
        except CrisisAlert.DoesNotExist:
            pass


class AdminMonitoringConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for admin dashboard monitoring.
    Provides real-time updates for admin statistics and system status.
    """
    
    async def connect(self):
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated or self.user.role != 'admin':
            await self.close()
            return
        
        # Join admin monitoring group
        await self.channel_layer.group_add(
            'admin_monitoring',
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial dashboard data
        await self.send_dashboard_data()
    
    async def disconnect(self, close_code):
        # Leave admin monitoring group
        await self.channel_layer.group_discard(
            'admin_monitoring',
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            request_type = data.get('type')
            
            if request_type == 'refresh_dashboard':
                await self.send_dashboard_data()
            elif request_type == 'get_user_stats':
                await self.send_user_statistics()
            elif request_type == 'get_system_health':
                await self.send_system_health()
                
        except json.JSONDecodeError:
            pass
    
    # WebSocket message handlers
    async def dashboard_update(self, event):
        """Send dashboard update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data']
        }, cls=DjangoJSONEncoder))
    
    async def system_alert(self, event):
        """Send system alert to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'system_alert',
            'data': event['alert']
        }, cls=DjangoJSONEncoder))
    
    @database_sync_to_async
    def send_dashboard_data(self):
        """Send comprehensive dashboard data"""
        # Implementation for dashboard data
        pass
    
    @database_sync_to_async
    def send_user_statistics(self):
        """Send user statistics"""
        # Implementation for user stats
        pass
    
    @database_sync_to_async
    def send_system_health(self):
        """Send system health metrics"""
        # Implementation for system health
        pass