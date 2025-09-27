"""
Serializers for the core app.
Handles system management, notifications, FAQs, and analytics.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import (
    SystemConfiguration, AuditLog, Notification, FAQ,
    ContactMessage, SystemAlert, UserPreference, Analytics
)

User = get_user_model()


class SystemConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for system configuration"""
    parsed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'id', 'key', 'value', 'parsed_value', 'description',
            'data_type', 'is_public', 'is_editable', 'category',
            'created_at', 'updated_at', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by']
    
    def get_parsed_value(self, obj):
        return obj.get_value()


class PublicSystemConfigurationSerializer(serializers.ModelSerializer):
    """Public system configuration (limited fields)"""
    parsed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemConfiguration
        fields = ['key', 'parsed_value', 'description', 'category']
    
    def get_parsed_value(self, obj):
        return obj.get_value()


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    user_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_display', 'action_type', 'action_description',
            'model_name', 'object_id', 'object_repr', 'ip_address',
            'was_successful', 'error_message', 'additional_data', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return "System"


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    sender_name = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority',
            'action_url', 'action_data', 'is_read', 'read_at',
            'sender_name', 'time_ago', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'sender_name', 'time_ago']
    
    def get_sender_name(self, obj):
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.username
        return "System"
    
    def get_time_ago(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'recipient', 'title', 'message', 'notification_type',
            'priority', 'action_url', 'action_data', 'send_email',
            'send_push', 'scheduled_for'
        ]
    
    def validate_recipient(self, value):
        # Ensure recipient exists and is active
        if not value.is_active:
            raise serializers.ValidationError("Recipient user is not active")
        return value


class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQs"""
    created_by_name = serializers.SerializerMethodField()
    helpfulness_ratio = serializers.SerializerMethodField()
    
    class Meta:
        model = FAQ
        fields = [
            'id', 'question', 'answer', 'category', 'order',
            'is_featured', 'is_published', 'search_keywords',
            'view_count', 'helpful_count', 'not_helpful_count',
            'helpfulness_ratio', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'view_count', 'helpful_count', 'not_helpful_count',
            'created_at', 'updated_at', 'created_by_name', 'helpfulness_ratio'
        ]
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_helpfulness_ratio(self, obj):
        total_votes = obj.helpful_count + obj.not_helpful_count
        if total_votes == 0:
            return 0
        return round((obj.helpful_count / total_votes) * 100, 1)


class FAQCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating FAQs"""
    
    class Meta:
        model = FAQ
        fields = [
            'question', 'answer', 'category', 'order',
            'is_featured', 'is_published', 'search_keywords'
        ]


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for contact messages"""
    sender_name_display = serializers.SerializerMethodField()
    time_since_created = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'sender', 'sender_name', 'sender_email', 'sender_phone',
            'sender_name_display', 'message_type', 'subject', 'message',
            'status', 'priority', 'assigned_to', 'assigned_to_name',
            'response', 'response_sent_at', 'time_since_created',
            'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'sender_name_display',
            'time_since_created', 'assigned_to_name'
        ]
    
    def get_sender_name_display(self, obj):
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.username
        return obj.sender_name or obj.sender_email
    
    def get_time_since_created(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        else:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contact messages"""
    
    class Meta:
        model = ContactMessage
        fields = [
            'sender_name', 'sender_email', 'sender_phone',
            'message_type', 'subject', 'message'
        ]
    
    def validate(self, attrs):
        # If user is not authenticated, require contact information
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            if not attrs.get('sender_email'):
                raise serializers.ValidationError(
                    "Email is required for anonymous messages"
                )
            if not attrs.get('sender_name'):
                raise serializers.ValidationError(
                    "Name is required for anonymous messages"
                )
        return attrs


class SystemAlertSerializer(serializers.ModelSerializer):
    """Serializer for system alerts"""
    created_by_name = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemAlert
        fields = [
            'id', 'title', 'message', 'alert_type', 'status',
            'target_roles', 'is_dismissible', 'show_on_login',
            'show_on_dashboard', 'start_time', 'end_time',
            'created_by_name', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_name', 'is_active']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_is_active(self, obj):
        now = timezone.now()
        if obj.status != 'active':
            return False
        if obj.start_time > now:
            return False
        if obj.end_time and obj.end_time < now:
            return False
        return True


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user preferences"""
    
    class Meta:
        model = UserPreference
        fields = [
            'email_notifications', 'push_notifications', 'sms_notifications',
            'appointment_reminders', 'wellness_reminders', 'community_notifications',
            'assessment_reminders', 'crisis_alerts', 'profile_visibility',
            'show_online_status', 'allow_direct_messages', 'theme',
            'language', 'timezone', 'dashboard_widgets', 'dashboard_layout',
            'data_sharing_analytics', 'data_sharing_research'
        ]


class AnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for analytics data"""
    user_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Analytics
        fields = [
            'id', 'metric_type', 'metric_name', 'metric_key',
            'value', 'unit', 'additional_data', 'user_display',
            'period', 'period_start', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp', 'user_display']
    
    def get_user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None


class SystemStatsSerializer(serializers.Serializer):
    """Serializer for system statistics"""
    user_stats = serializers.DictField()
    activity_stats = serializers.DictField()
    engagement_stats = serializers.DictField()
    system_health = serializers.DictField()
    recent_activity = serializers.ListField()


class DashboardDataSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    notifications = NotificationSerializer(many=True)
    system_alerts = SystemAlertSerializer(many=True)
    quick_stats = serializers.DictField()
    recent_activity = serializers.ListField()
    user_preferences = UserPreferenceSerializer()


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_priority = serializers.DictField()
    recent_notifications = NotificationSerializer(many=True)