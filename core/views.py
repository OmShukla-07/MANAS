"""
API views for the core app.
Handles system management, notifications, FAQs, and analytics.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

# Supabase views disabled (not using Supabase)
# from .supabase_views import (
#     supabase_status, migrate_to_supabase, 
#     supabase_setup_guide, supabase_dashboard_view
# )
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q, Max, F
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.cache import cache

from .models import (
    SystemConfiguration, AuditLog, Notification, FAQ,
    ContactMessage, SystemAlert, UserPreference, Analytics
)
from .serializers import (
    SystemConfigurationSerializer, PublicSystemConfigurationSerializer,
    AuditLogSerializer, NotificationSerializer, NotificationCreateSerializer,
    FAQSerializer, FAQCreateUpdateSerializer, ContactMessageSerializer,
    ContactMessageCreateSerializer, SystemAlertSerializer,
    UserPreferenceSerializer, AnalyticsSerializer, SystemStatsSerializer,
    DashboardDataSerializer, NotificationStatsSerializer
)

User = get_user_model()


# System Configuration
class SystemConfigurationListView(generics.ListAPIView):
    """List system configurations (admin only)"""
    queryset = SystemConfiguration.objects.all().order_by('category', 'key')
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can view system configurations")
        
        category = self.request.query_params.get('category')
        if category:
            return self.queryset.filter(category=category)
        return self.queryset


class PublicSystemConfigurationView(generics.ListAPIView):
    """List public system configurations"""
    queryset = SystemConfiguration.objects.filter(is_public=True).order_by('category', 'key')
    serializer_class = PublicSystemConfigurationSerializer
    permission_classes = [permissions.AllowAny]


class SystemConfigurationDetailView(generics.RetrieveUpdateAPIView):
    """Detailed view of system configuration (admin only)"""
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can modify system configurations")
        return super().get_object()
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# Audit Logs
class AuditLogListView(generics.ListAPIView):
    """List audit logs (admin/counselor only)"""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role not in ['admin', 'counselor']:
            raise permissions.PermissionDenied("Access denied")
        
        queryset = AuditLog.objects.all()
        
        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by model
        model_name = self.request.query_params.get('model')
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
        # Filter by date range
        days = self.request.query_params.get('days', 30)
        try:
            days = int(days)
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(timestamp__gte=start_date)
        except ValueError:
            pass
        
        # Filter by success status
        if self.request.query_params.get('failed_only'):
            queryset = queryset.filter(was_successful=False)
        
        return queryset.order_by('-timestamp')


# Notifications
class NotificationListView(generics.ListAPIView):
    """List user notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read = is_read.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_read=is_read)
        
        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Limit recent notifications
        days = self.request.query_params.get('days', 30)
        try:
            days = int(days)
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created_at__gte=start_date)
        except ValueError:
            pass
        
        return queryset.order_by('-created_at')


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    """Detailed view of notification"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Mark as read if not already
        if not instance.is_read:
            instance.is_read = True
            instance.read_at = timezone.now()
            instance.save(update_fields=['is_read', 'read_at'])
        
        return super().retrieve(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notifications_read(request):
    """Mark multiple notifications as read"""
    notification_ids = request.data.get('notification_ids', [])
    
    if notification_ids:
        # Mark specific notifications as read
        updated = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
    else:
        # Mark all unread notifications as read
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
    
    return Response({
        'message': f'Marked {updated} notifications as read'
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_notifications(request):
    """Delete multiple notifications"""
    notification_ids = request.data.get('notification_ids', [])
    
    if notification_ids:
        deleted_count, _ = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user
        ).delete()
    else:
        # Delete all read notifications older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count, _ = Notification.objects.filter(
            recipient=request.user,
            is_read=True,
            created_at__lt=cutoff_date
        ).delete()
    
    return Response({
        'message': f'Deleted {deleted_count} notifications'
    })


class NotificationCreateView(generics.CreateAPIView):
    """Create notification (admin/counselor only)"""
    serializer_class = NotificationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        if self.request.user.role not in ['admin', 'counselor']:
            raise permissions.PermissionDenied("Only admins and counselors can create notifications")
        
        serializer.save(sender=self.request.user)


# FAQs
class FAQListView(generics.ListAPIView):
    """List FAQs"""
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = FAQ.objects.filter(is_published=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Search in questions and answers
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(question__icontains=search) |
                Q(answer__icontains=search) |
                Q(search_keywords__contains=[search])
            )
        
        # Show featured first
        if self.request.query_params.get('featured_first'):
            queryset = queryset.order_by('-is_featured', 'order', 'question')
        else:
            queryset = queryset.order_by('category', 'order', 'question')
        
        return queryset


class FAQDetailView(generics.RetrieveAPIView):
    """Detailed view of FAQ"""
    queryset = FAQ.objects.filter(is_published=True)
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        instance.view_count = F('view_count') + 1
        instance.save(update_fields=['view_count'])
        
        return super().retrieve(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def rate_faq_helpfulness(request, faq_id):
    """Rate FAQ helpfulness"""
    try:
        faq = FAQ.objects.get(id=faq_id, is_published=True)
        is_helpful = request.data.get('is_helpful', True)
        
        if is_helpful:
            faq.helpful_count = F('helpful_count') + 1
        else:
            faq.not_helpful_count = F('not_helpful_count') + 1
        
        faq.save(update_fields=['helpful_count' if is_helpful else 'not_helpful_count'])
        
        return Response({'message': 'Thank you for your feedback'})
        
    except FAQ.DoesNotExist:
        return Response({'error': 'FAQ not found'}, status=status.HTTP_404_NOT_FOUND)


class FAQManagementListCreateView(generics.ListCreateAPIView):
    """Manage FAQs (admin/counselor only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FAQCreateUpdateSerializer
        return FAQSerializer
    
    def get_queryset(self):
        if self.request.user.role not in ['admin', 'counselor']:
            raise permissions.PermissionDenied("Access denied")
        
        return FAQ.objects.all().order_by('category', 'order', 'question')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FAQManagementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage FAQ detail (admin/counselor only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return FAQCreateUpdateSerializer
        return FAQSerializer
    
    def get_queryset(self):
        if self.request.user.role not in ['admin', 'counselor']:
            raise permissions.PermissionDenied("Access denied")
        
        return FAQ.objects.all()


# Contact Messages
class ContactMessageCreateView(generics.CreateAPIView):
    """Create contact message"""
    serializer_class = ContactMessageCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        # Capture request metadata
        request = self.context.get('request', self.request)
        additional_data = {}
        
        if hasattr(request, 'META'):
            additional_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
            
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        # Auto-assign priority based on message type
        message_type = serializer.validated_data.get('message_type')
        priority = 'urgent' if message_type == 'emergency' else 'medium'
        
        serializer.save(
            sender=request.user if request.user.is_authenticated else None,
            priority=priority,
            ip_address=ip_address,
            user_agent=additional_data.get('user_agent', ''),
            additional_data=additional_data
        )


class ContactMessageListView(generics.ListAPIView):
    """List contact messages (admin/counselor only)"""
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role not in ['admin', 'counselor']:
            raise permissions.PermissionDenied("Access denied")
        
        queryset = ContactMessage.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by message type
        message_type = self.request.query_params.get('type')
        if message_type:
            queryset = queryset.filter(message_type=message_type)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by assignment
        if self.request.query_params.get('unassigned'):
            queryset = queryset.filter(assigned_to__isnull=True)
        elif self.request.query_params.get('my_assignments'):
            queryset = queryset.filter(assigned_to=self.request.user)
        
        return queryset.order_by('-priority', '-created_at')


class ContactMessageDetailView(generics.RetrieveUpdateAPIView):
    """Detailed view of contact message (admin/counselor only)"""
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role not in ['admin', 'counselor']:
            raise permissions.PermissionDenied("Access denied")
        
        return ContactMessage.objects.all()


# System Alerts
class SystemAlertListView(generics.ListAPIView):
    """List active system alerts"""
    serializer_class = SystemAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        now = timezone.now()
        queryset = SystemAlert.objects.filter(
            status='active',
            start_time__lte=now
        ).filter(
            Q(end_time__isnull=True) | Q(end_time__gte=now)
        )
        
        # Filter by user role if targeting specific roles
        user_role = self.request.user.role
        queryset = queryset.filter(
            Q(target_roles=[]) | Q(target_roles__contains=[user_role])
        )
        
        # Filter by specific targeting
        queryset = queryset.filter(
            Q(target_users__isnull=True) | Q(target_users=self.request.user)
        )
        
        return queryset.order_by('-start_time')


class SystemAlertManagementView(generics.ListCreateAPIView):
    """Manage system alerts (admin only)"""
    serializer_class = SystemAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can manage system alerts")
        
        return SystemAlert.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# User Preferences
class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """User preferences management"""
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        preferences, created = UserPreference.objects.get_or_create(
            user=self.request.user
        )
        return preferences


# Analytics
class AnalyticsView(generics.ListCreateAPIView):
    """Analytics data (admin/counselor only for viewing)"""
    serializer_class = AnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role not in ['admin', 'counselor']:
            # Regular users can only see their own analytics
            queryset = Analytics.objects.filter(user=self.request.user)
        else:
            queryset = Analytics.objects.all()
        
        # Filter by metric type
        metric_type = self.request.query_params.get('metric_type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        # Filter by time range
        days = self.request.query_params.get('days', 30)
        try:
            days = int(days)
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(timestamp__gte=start_date)
        except ValueError:
            pass
        
        return queryset.order_by('-timestamp')


# Dashboard
class DashboardView(APIView):
    """User dashboard data"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Recent notifications (unread first)
        notifications = Notification.objects.filter(
            recipient=user
        ).order_by('is_read', '-created_at')[:10]
        
        # Active system alerts
        now = timezone.now()
        system_alerts = SystemAlert.objects.filter(
            status='active',
            start_time__lte=now,
            show_on_dashboard=True
        ).filter(
            Q(end_time__isnull=True) | Q(end_time__gte=now)
        ).filter(
            Q(target_roles=[]) | Q(target_roles__contains=[user.role])
        )[:5]
        
        # Quick stats based on user role
        quick_stats = self._get_user_quick_stats(user)
        
        # Recent activity (simplified)
        recent_activity = self._get_recent_activity(user)
        
        # User preferences
        preferences, _ = UserPreference.objects.get_or_create(user=user)
        
        dashboard_data = {
            'notifications': NotificationSerializer(notifications, many=True).data,
            'system_alerts': SystemAlertSerializer(system_alerts, many=True).data,
            'quick_stats': quick_stats,
            'recent_activity': recent_activity,
            'user_preferences': UserPreferenceSerializer(preferences).data
        }
        
        return Response(dashboard_data)
    
    def _get_user_quick_stats(self, user):
        """Get quick stats based on user role"""
        stats = {
            'unread_notifications': Notification.objects.filter(
                recipient=user, is_read=False
            ).count()
        }
        
        if user.role == 'student':
            # Student-specific stats
            from appointments.models import Appointment
            from wellness.models import MoodEntry
            
            stats.update({
                'upcoming_appointments': Appointment.objects.filter(
                    student=user,
                    appointment_date__gte=timezone.now(),
                    status='confirmed'
                ).count(),
                'mood_entries_this_week': MoodEntry.objects.filter(
                    user=user,
                    date__gte=timezone.now().date() - timedelta(days=7)
                ).count()
            })
        
        elif user.role == 'counselor':
            # Counselor-specific stats
            from appointments.models import Appointment
            from crisis.models import CrisisAlert
            
            stats.update({
                'todays_appointments': Appointment.objects.filter(
                    counselor=user,
                    appointment_date__date=timezone.now().date(),
                    status='confirmed'
                ).count(),
                'active_crisis_alerts': CrisisAlert.objects.filter(
                    assigned_counselor=user,
                    status='active'
                ).count(),
                'pending_follow_ups': 0  # Would be calculated based on your follow-up system
            })
        
        elif user.role == 'admin':
            # Admin-specific stats
            stats.update({
                'total_users': User.objects.filter(is_active=True).count(),
                'new_users_today': User.objects.filter(
                    date_joined__date=timezone.now().date()
                ).count(),
                'pending_contact_messages': ContactMessage.objects.filter(
                    status='new'
                ).count()
            })
        
        return stats
    
    def _get_recent_activity(self, user):
        """Get recent user activity"""
        activities = []
        
        # Recent audit logs for this user
        recent_logs = AuditLog.objects.filter(
            user=user
        ).order_by('-timestamp')[:5]
        
        for log in recent_logs:
            activities.append({
                'type': 'activity',
                'description': log.action_description,
                'timestamp': log.timestamp,
                'success': log.was_successful
            })
        
        return activities


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def system_stats(request):
    """Get system statistics (admin only)"""
    if request.user.role != 'admin':
        return Response(
            {"error": "Only admins can view system statistics"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Cache stats for 1 hour
    cache_key = 'system_stats'
    cached_stats = cache.get(cache_key)
    if cached_stats:
        return Response(cached_stats)
    
    # Calculate stats
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    user_stats = {
        'total_users': User.objects.filter(is_active=True).count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'new_users_this_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
        'users_by_role': dict(User.objects.filter(is_active=True).values_list('role').annotate(Count('role')))
    }
    
    activity_stats = {
        'total_audit_logs': AuditLog.objects.count(),
        'activities_today': AuditLog.objects.filter(timestamp__date=today).count(),
        'failed_actions_today': AuditLog.objects.filter(
            timestamp__date=today, was_successful=False
        ).count()
    }
    
    engagement_stats = {
        'total_notifications': Notification.objects.count(),
        'notifications_sent_today': Notification.objects.filter(created_at__date=today).count(),
        'contact_messages_pending': ContactMessage.objects.filter(status='new').count(),
        'faq_views_this_month': FAQ.objects.aggregate(
            total_views=Count('view_count')
        )['total_views'] or 0
    }
    
    system_health = {
        'active_alerts': SystemAlert.objects.filter(status='active').count(),
        'system_errors_today': AuditLog.objects.filter(
            timestamp__date=today,
            was_successful=False,
            action_type='admin_action'
        ).count(),
        'database_size': 'N/A',  # Would require database-specific queries
        'cache_hit_rate': 'N/A'  # Would require cache statistics
    }
    
    recent_activity = list(AuditLog.objects.order_by('-timestamp')[:10].values(
        'action_description', 'timestamp', 'was_successful', 'user__username'
    ))
    
    stats = {
        'user_stats': user_stats,
        'activity_stats': activity_stats,
        'engagement_stats': engagement_stats,
        'system_health': system_health,
        'recent_activity': recent_activity
    }
    
    # Cache for 1 hour
    cache.set(cache_key, stats, 3600)
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """Get notification statistics for current user"""
    user = request.user
    
    total_notifications = Notification.objects.filter(recipient=user).count()
    unread_notifications = Notification.objects.filter(
        recipient=user, is_read=False
    ).count()
    
    # Notifications by type
    notifications_by_type = dict(
        Notification.objects.filter(recipient=user).values(
            'notification_type'
        ).annotate(count=Count('id')).values_list('notification_type', 'count')
    )
    
    # Notifications by priority
    notifications_by_priority = dict(
        Notification.objects.filter(recipient=user).values(
            'priority'
        ).annotate(count=Count('id')).values_list('priority', 'count')
    )
    
    # Recent notifications
    recent_notifications = Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:5]
    
    stats = {
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'notifications_by_type': notifications_by_type,
        'notifications_by_priority': notifications_by_priority,
        'recent_notifications': NotificationSerializer(recent_notifications, many=True).data
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_dashboard_stats(request):
    """Get enhanced admin dashboard statistics"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    # Cache key for dashboard stats
    cache_key = 'admin_dashboard_stats'
    cached_stats = cache.get(cache_key)
    
    if cached_stats:
        return Response(cached_stats)
    
    # Calculate statistics
    total_users = User.objects.count()
    
    # Active sessions (users who logged in within last 24 hours)
    yesterday = timezone.now() - timedelta(days=1)
    active_sessions = User.objects.filter(last_login__gte=yesterday).count()
    
    # Crisis alerts from crisis app
    crisis_alerts = 0
    try:
        from crisis.models import CrisisAlert
        crisis_alerts = CrisisAlert.objects.filter(
            status__in=['open', 'in_progress'], is_resolved=False
        ).count()
    except ImportError:
        pass
    
    # Reports generated this month
    this_month = timezone.now().replace(day=1)
    reports_generated = AuditLog.objects.filter(
        action__icontains='report', timestamp__gte=this_month
    ).count()
    
    # User satisfaction (mock data for now)
    user_satisfaction = 94.2
    
    # Average response time (mock data)
    avg_response_time = 156
    
    stats = {
        'total_users': total_users,
        'active_sessions': active_sessions,
        'crisis_alerts': crisis_alerts,
        'reports_generated': reports_generated,
        'user_satisfaction': user_satisfaction,
        'avg_response_time': avg_response_time,
        'last_updated': timezone.now().isoformat()
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, stats, 300)
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_recent_activity(request):
    """Get recent activity for admin dashboard"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get recent audit logs and other activities
    recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    activities = []
    for log in recent_logs:
        activity_type = 'info'
        icon = '<svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20"><path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4z"/></svg>'
        
        if 'user' in log.action.lower() and 'create' in log.action.lower():
            activity_type = 'success'
            icon = '<svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
        elif 'crisis' in log.action.lower() or 'alert' in log.action.lower():
            activity_type = 'warning'
            icon = '<svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20"><path d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92z"/></svg>'
        elif 'error' in log.action.lower() or 'fail' in log.action.lower():
            activity_type = 'error'
            icon = '<svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"/></svg>'
        
        # Calculate time ago
        time_diff = timezone.now() - log.timestamp
        if time_diff.days > 0:
            timestamp = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            timestamp = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            timestamp = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            timestamp = "Just now"
        
        activities.append({
            'title': log.action.replace('_', ' ').title(),
            'description': f"User: {log.user.get_full_name() if log.user else 'System'}" if log.details else log.action,
            'timestamp': timestamp,
            'type': activity_type,
            'icon': icon
        })
    
    return Response(activities)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_system_health(request):
    """Get system health metrics for admin dashboard"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    # System health metrics (mock data for now - in production, integrate with monitoring systems)
    health_data = {
        'server_status': {
            'status': 'online',
            'uptime': '99.9%',
            'response_time': '156ms',
            'last_check': timezone.now().isoformat()
        },
        'database': {
            'status': 'healthy',
            'connections': 45,
            'response_time': '2.3ms',
            'last_check': timezone.now().isoformat()
        },
        'api_performance': {
            'status': 'slow',
            'avg_response_time': '450ms',
            'requests_per_minute': 234,
            'last_check': timezone.now().isoformat()
        },
        'storage': {
            'status': 'normal',
            'used_percentage': 67,
            'free_space': '2.1TB',
            'last_check': timezone.now().isoformat()
        },
        'overall_status': 'operational'
    }
    
    return Response(health_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_user_action_ajax(request):
    """Handle AJAX requests for user management actions"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    action = request.data.get('action')
    user_id = request.data.get('user_id')
    user_ids = request.data.get('user_ids', [])
    
    try:
        # Handle bulk actions
        if action and user_ids and action.startswith('bulk_'):
            target_users = User.objects.filter(id__in=user_ids).exclude(id=request.user.id)
            
            if action == 'bulk_activate':
                count = target_users.update(is_active=True)
                return Response({'success': True, 'message': f"Activated {count} users successfully."})
            
            elif action == 'bulk_deactivate':
                count = target_users.update(is_active=False)
                return Response({'success': True, 'message': f"Deactivated {count} users successfully."})
            
            elif action == 'bulk_verify':
                count = target_users.update(is_verified=True)
                return Response({'success': True, 'message': f"Verified {count} users successfully."})
            
            elif action == 'bulk_delete':
                count = target_users.count()
                target_users.delete()
                return Response({'success': True, 'message': f"Deleted {count} users successfully."})
        
        # Handle single user actions
        elif action and user_id:
            target_user = User.objects.get(id=user_id)
            
            if action == 'activate':
                target_user.is_active = True
                target_user.save()
                return Response({'success': True, 'message': f"User {target_user.get_full_name()} has been activated."})
            
            elif action == 'deactivate':
                if target_user != request.user:
                    target_user.is_active = False
                    target_user.save()
                    return Response({'success': True, 'message': f"User {target_user.get_full_name()} has been deactivated."})
                else:
                    return Response({'error': 'You cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)
            
            elif action == 'verify':
                target_user.is_verified = True
                target_user.save()
                return Response({'success': True, 'message': f"User {target_user.get_full_name()} has been verified."})
            
            elif action == 'unverify':
                target_user.is_verified = False
                target_user.save()
                return Response({'success': True, 'message': f"User {target_user.get_full_name()} has been unverified."})
            
            elif action == 'change_role':
                new_role = request.data.get('new_role')
                if new_role and new_role in ['student', 'counselor', 'admin']:
                    old_role = target_user.role
                    target_user.role = new_role
                    target_user.save()
                    return Response({'success': True, 'message': f"User {target_user.get_full_name()} role changed from {old_role} to {new_role}."})
                else:
                    return Response({'error': 'Invalid role specified.'}, status=status.HTTP_400_BAD_REQUEST)
            
            elif action == 'reset_password':
                import string
                import random
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                target_user.set_password(temp_password)
                target_user.save()
                return Response({'success': True, 'message': f"Password reset for {target_user.get_full_name()}. Temporary password: {temp_password}"})
            
            elif action == 'delete':
                if target_user != request.user:
                    username = target_user.get_full_name()
                    target_user.delete()
                    return Response({'success': True, 'message': f"User {username} has been deleted."})
                else:
                    return Response({'error': 'You cannot delete your own account.'}, status=status.HTTP_400_BAD_REQUEST)
    
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f"Error performing action: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({'error': 'Invalid action or parameters.'}, status=status.HTTP_400_BAD_REQUEST)
