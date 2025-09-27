"""
Serializers for the crisis app.
Handles crisis detection, alerts, safety plans, and emergency resources.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import (
    CrisisType, CrisisAlert, CrisisResponse, SafetyPlan, 
    CrisisResource, CrisisFollowUp, CrisisAnalytics
)

User = get_user_model()


class CrisisTypeSerializer(serializers.ModelSerializer):
    """Serializer for crisis types"""
    
    class Meta:
        model = CrisisType
        fields = [
            'id', 'name', 'description', 'severity_level', 'trigger_keywords',
            'behavioral_indicators', 'emotional_indicators', 'immediate_response',
            'escalation_criteria', 'requires_immediate_intervention', 'auto_escalate'
        ]


class CrisisAlertListSerializer(serializers.ModelSerializer):
    """Serializer for listing crisis alerts"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    crisis_type_name = serializers.CharField(source='crisis_type.name', read_only=True)
    assigned_counselor_name = serializers.CharField(source='assigned_counselor.get_full_name', read_only=True)
    time_since_created = serializers.SerializerMethodField()
    urgency_level = serializers.SerializerMethodField()
    
    class Meta:
        model = CrisisAlert
        fields = [
            'id', 'user', 'user_name', 'crisis_type', 'crisis_type_name',
            'status', 'source', 'severity_level', 'confidence_score',
            'description', 'assigned_counselor', 'assigned_counselor_name',
            'urgency_level', 'time_since_created', 'created_at'
        ]
    
    def get_time_since_created(self, obj):
        """Calculate time since alert was created"""
        delta = timezone.now() - obj.created_at
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hours ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    def get_urgency_level(self, obj):
        """Calculate urgency based on severity and time"""
        base_urgency = obj.severity_level
        time_factor = (timezone.now() - obj.created_at).total_seconds() / 3600  # hours
        
        if obj.status == 'active' and time_factor > 2:  # Unresponded for 2+ hours
            base_urgency += 2
        
        return min(base_urgency, 10)


class CrisisAlertDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for crisis alerts"""
    user = serializers.StringRelatedField(read_only=True)
    crisis_type = CrisisTypeSerializer(read_only=True)
    assigned_counselor = serializers.StringRelatedField(read_only=True)
    responses = serializers.SerializerMethodField()
    follow_ups = serializers.SerializerMethodField()
    
    class Meta:
        model = CrisisAlert
        fields = [
            'id', 'user', 'crisis_type', 'status', 'source', 'severity_level',
            'confidence_score', 'description', 'detected_keywords', 'context_data',
            'chat_session', 'message', 'assessment', 'assigned_counselor',
            'response_time', 'resolution_time', 'created_at', 'acknowledged_at',
            'resolved_at', 'follow_up_required', 'follow_up_date',
            'responses', 'follow_ups'
        ]
    
    def get_responses(self, obj):
        responses = obj.responses.all().order_by('-created_at')
        return CrisisResponseSerializer(responses, many=True).data
    
    def get_follow_ups(self, obj):
        follow_ups = obj.follow_ups.all().order_by('-scheduled_date')
        return CrisisFollowUpSerializer(follow_ups, many=True).data


class CrisisAlertCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating crisis alerts"""
    
    class Meta:
        model = CrisisAlert
        fields = [
            'user', 'crisis_type', 'source', 'severity_level',
            'description', 'context_data', 'chat_session', 'message', 'assessment'
        ]
        
    def create(self, validated_data):
        # Set confidence score based on source
        source = validated_data.get('source')
        if source == 'ai_detection':
            validated_data['confidence_score'] = 0.85
        elif source == 'self_report':
            validated_data['confidence_score'] = 1.0
        elif source == 'counselor_assessment':
            validated_data['confidence_score'] = 0.95
        else:
            validated_data['confidence_score'] = 0.7
        
        return super().create(validated_data)


class CrisisResponseSerializer(serializers.ModelSerializer):
    """Serializer for crisis responses"""
    responder_name = serializers.CharField(source='responder.get_full_name', read_only=True)
    
    class Meta:
        model = CrisisResponse
        fields = [
            'id', 'alert', 'responder', 'responder_name', 'response_type',
            'description', 'actions_taken', 'was_effective', 'user_response',
            'next_steps', 'resources_provided', 'contacts_made',
            'response_time', 'created_at'
        ]


class CrisisResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating crisis responses"""
    
    class Meta:
        model = CrisisResponse
        fields = [
            'alert', 'response_type', 'description', 'actions_taken',
            'was_effective', 'user_response', 'next_steps',
            'resources_provided', 'contacts_made'
        ]
    
    def create(self, validated_data):
        alert = validated_data['alert']
        responder = self.context['request'].user
        
        # Calculate response time
        response_time = timezone.now() - alert.created_at
        validated_data['response_time'] = response_time
        validated_data['responder'] = responder
        
        # Update alert status
        if alert.status == 'active':
            alert.status = 'acknowledged'
            alert.acknowledged_at = timezone.now()
            alert.assigned_counselor = responder
            alert.save()
        
        return super().create(validated_data)


class SafetyPlanSerializer(serializers.ModelSerializer):
    """Serializer for safety plans"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    needs_review = serializers.SerializerMethodField()
    
    class Meta:
        model = SafetyPlan
        fields = [
            'id', 'user', 'user_name', 'created_by', 'created_by_name',
            'title', 'status', 'warning_signs', 'triggers', 'coping_strategies',
            'safe_spaces', 'support_contacts', 'professional_contacts',
            'crisis_hotlines', 'lethal_means_restriction', 'environmental_safety',
            'emergency_procedures', 'when_to_call_911', 'last_reviewed',
            'review_frequency_days', 'times_activated', 'needs_review',
            'created_at', 'updated_at'
        ]
    
    def get_needs_review(self, obj):
        return obj.needs_review()


class SafetyPlanCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating safety plans"""
    
    class Meta:
        model = SafetyPlan
        fields = [
            'user', 'title', 'status', 'warning_signs', 'triggers',
            'coping_strategies', 'safe_spaces', 'support_contacts',
            'professional_contacts', 'crisis_hotlines', 'lethal_means_restriction',
            'environmental_safety', 'emergency_procedures', 'when_to_call_911',
            'review_frequency_days'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CrisisResourceSerializer(serializers.ModelSerializer):
    """Serializer for crisis resources"""
    applicable_crisis_types = serializers.StringRelatedField(source='crisis_types', many=True, read_only=True)
    
    class Meta:
        model = CrisisResource
        fields = [
            'id', 'name', 'description', 'resource_type', 'phone_number',
            'text_number', 'email', 'website_url', 'chat_url', 'availability',
            'availability_details', 'location', 'serves_areas', 'target_demographics',
            'applicable_crisis_types', 'languages_supported', 'is_verified',
            'is_free', 'requires_insurance', 'rating', 'is_featured'
        ]


class CrisisResourceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing crisis resources"""
    
    class Meta:
        model = CrisisResource
        fields = [
            'id', 'name', 'description', 'resource_type', 'phone_number',
            'availability', 'is_free', 'is_featured', 'rating'
        ]


class CrisisFollowUpSerializer(serializers.ModelSerializer):
    """Serializer for crisis follow-ups"""
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    alert_user_name = serializers.CharField(source='alert.user.get_full_name', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = CrisisFollowUp
        fields = [
            'id', 'alert', 'alert_user_name', 'assigned_to', 'assigned_to_name',
            'follow_up_type', 'status', 'scheduled_date', 'purpose', 'notes',
            'outcome', 'user_status', 'additional_support_needed', 'new_concerns',
            'next_follow_up_date', 'recommendations', 'is_overdue',
            'created_at', 'completed_at'
        ]
    
    def get_is_overdue(self, obj):
        return obj.scheduled_date < timezone.now() and obj.status == 'scheduled'


class CrisisFollowUpCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating crisis follow-ups"""
    
    class Meta:
        model = CrisisFollowUp
        fields = [
            'alert', 'follow_up_type', 'scheduled_date', 'purpose'
        ]
    
    def create(self, validated_data):
        validated_data['assigned_to'] = self.context['request'].user
        return super().create(validated_data)


class CrisisAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for crisis analytics"""
    
    class Meta:
        model = CrisisAnalytics
        fields = [
            'id', 'start_date', 'end_date', 'total_alerts', 'high_severity_alerts',
            'false_positives', 'ai_detected_alerts', 'average_response_time',
            'average_resolution_time', 'escalation_rate', 'successful_interventions',
            'follow_up_completion_rate', 'crisis_types_breakdown', 'peak_hours',
            'demographic_breakdown', 'ai_accuracy_rate', 'ai_precision',
            'ai_recall', 'system_recommendations', 'generated_at'
        ]


# Dashboard serializers
class CrisisDashboardSerializer(serializers.Serializer):
    """Crisis management dashboard data"""
    active_alerts = CrisisAlertListSerializer(many=True)
    high_priority_alerts = CrisisAlertListSerializer(many=True)
    recent_alerts = CrisisAlertListSerializer(many=True)
    pending_follow_ups = CrisisFollowUpSerializer(many=True)
    stats = serializers.DictField()


class CrisisStatsSerializer(serializers.Serializer):
    """Crisis statistics"""
    total_alerts_today = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    high_severity_alerts = serializers.IntegerField()
    average_response_time_minutes = serializers.FloatField()
    alerts_by_type = serializers.DictField()
    alerts_by_hour = serializers.ListField()
    resolution_rate = serializers.FloatField()


class UserCrisisStatusSerializer(serializers.Serializer):
    """User's crisis-related status for counselors"""
    has_active_alerts = serializers.BooleanField()
    last_alert_date = serializers.DateTimeField()
    risk_level = serializers.CharField()
    safety_plan_status = serializers.CharField()
    recent_interventions = serializers.IntegerField()


# Emergency response serializers
class EmergencyContactSerializer(serializers.Serializer):
    """Emergency contact information"""
    name = serializers.CharField()
    phone = serializers.CharField()
    relationship = serializers.CharField()
    is_primary = serializers.BooleanField()


class QuickResponseActionSerializer(serializers.Serializer):
    """Quick response actions for crisis situations"""
    action_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    priority = serializers.IntegerField()
    requires_confirmation = serializers.BooleanField()


class CrisisInterventionSerializer(serializers.Serializer):
    """Immediate crisis intervention data"""
    intervention_type = serializers.CharField()
    message = serializers.CharField()
    resources = CrisisResourceListSerializer(many=True)
    contact_counselor = serializers.BooleanField()
    emergency_services = serializers.BooleanField()
    safety_plan_activation = serializers.BooleanField()