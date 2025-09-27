from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ChatSession, Message, AIPersonality, MessageReaction,
    ChatTemplate, ChatAnalytics
)

User = get_user_model()


class AIPersonalitySerializer(serializers.ModelSerializer):
    """Serializer for AI personality configurations"""
    
    class Meta:
        model = AIPersonality
        fields = [
            'id', 'name', 'description', 'personality_traits', 'response_style',
            'specialization_areas', 'greeting_message', 'crisis_response_template',
            'is_active', 'is_default'
        ]


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Serializer for chat session lists"""
    last_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    session_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_type', 'title', 'status', 'crisis_level',
            'created_at', 'updated_at', 'last_message_preview',
            'unread_count', 'session_duration'
        ]
    
    def get_last_message_preview(self, obj):
        last_message = obj.messages.last()
        if last_message:
            content = last_message.content[:100]
            return f"{content}..." if len(last_message.content) > 100 else content
        return "No messages yet"
    
    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()
    
    def get_session_duration(self, obj):
        if obj.ended_at:
            duration = obj.ended_at - obj.created_at
            return int(duration.total_seconds() / 60)  # in minutes
        return None


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for chat sessions"""
    counselor_name = serializers.SerializerMethodField()
    ai_personality = AIPersonalitySerializer(read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'user', 'counselor', 'counselor_name', 'ai_personality',
            'session_type', 'title', 'status', 'crisis_level',
            'requires_intervention', 'intervention_notes', 'session_summary',
            'tags', 'feedback_rating', 'feedback_comment', 'message_count',
            'created_at', 'updated_at', 'ended_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_counselor_name(self, obj):
        if obj.counselor:
            return obj.counselor.get_full_name()
        return None
    
    def get_message_count(self, obj):
        return obj.messages.count()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    reactions_count = serializers.SerializerMethodField()
    is_edited = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'session', 'sender', 'sender_name', 'sender_role',
            'content', 'message_type', 'ai_confidence_score',
            'contains_crisis_keywords', 'crisis_keywords_detected',
            'status', 'metadata', 'reactions_count', 'is_edited',
            'created_at', 'updated_at', 'is_read', 'read_at'
        ]
        read_only_fields = [
            'sender', 'ai_confidence_score', 'contains_crisis_keywords',
            'crisis_keywords_detected', 'created_at', 'updated_at'
        ]
    
    def get_sender_name(self, obj):
        if obj.sender:
            return obj.sender.get_full_name()
        return "MANAS AI"
    
    def get_sender_role(self, obj):
        if obj.sender:
            return obj.sender.role
        return "ai"
    
    def get_reactions_count(self, obj):
        return obj.reactions.count()
    
    def get_is_edited(self, obj):
        return obj.created_at != obj.updated_at


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new messages"""
    
    class Meta:
        model = Message
        fields = ['session', 'content', 'message_type', 'metadata']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class MessageReactionSerializer(serializers.ModelSerializer):
    """Serializer for message reactions"""
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'user_name', 'reaction_type', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()


class ChatTemplateSerializer(serializers.ModelSerializer):
    """Serializer for chat templates"""
    
    class Meta:
        model = ChatTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'content',
            'variables', 'conditions', 'is_active', 'usage_count'
        ]


class ChatAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for chat analytics"""
    
    class Meta:
        model = ChatAnalytics
        fields = [
            'id', 'session', 'total_messages', 'user_messages', 'ai_messages',
            'counselor_messages', 'session_duration_minutes', 'crisis_detected',
            'crisis_level', 'intervention_triggered', 'user_satisfaction',
            'resolution_status', 'topics_discussed', 'created_at'
        ]


class SessionStartSerializer(serializers.Serializer):
    """Serializer for starting new chat sessions"""
    session_type = serializers.ChoiceField(choices=ChatSession.SessionType.choices)
    title = serializers.CharField(max_length=200, required=False)
    ai_personality_id = serializers.IntegerField(required=False)
    initial_message = serializers.CharField(max_length=1000, required=False)
    
    def validate_ai_personality_id(self, value):
        if value:
            try:
                AIPersonality.objects.get(id=value, is_active=True)
            except AIPersonality.DoesNotExist:
                raise serializers.ValidationError("Invalid AI personality selected")
        return value


class SessionFeedbackSerializer(serializers.Serializer):
    """Serializer for session feedback"""
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=1000, required=False)
    helpful_aspects = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False
    )
    improvement_suggestions = serializers.CharField(max_length=500, required=False)


class CrisisDetectionSerializer(serializers.Serializer):
    """Serializer for crisis detection results"""
    crisis_detected = serializers.BooleanField()
    crisis_level = serializers.IntegerField(min_value=0, max_value=10)
    confidence_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    keywords_detected = serializers.ListField(child=serializers.CharField())
    recommended_actions = serializers.ListField(child=serializers.CharField())
    immediate_response = serializers.CharField()


class ChatStatsSerializer(serializers.Serializer):
    """Serializer for chat statistics"""
    total_sessions = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    completed_sessions = serializers.IntegerField()
    crisis_sessions = serializers.IntegerField()
    average_session_duration = serializers.FloatField()
    total_messages = serializers.IntegerField()
    user_satisfaction_average = serializers.FloatField()
    most_discussed_topics = serializers.ListField(child=serializers.CharField())


# AI Chatbot specific serializers
class ChatbotListSerializer(serializers.Serializer):
    """Serializer for available chatbot personalities"""
    type = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    avatar_emoji = serializers.CharField()
    color_theme = serializers.CharField()
    specialties = serializers.ListField(child=serializers.CharField())
    response_style = serializers.CharField()
    is_available = serializers.BooleanField(default=True)


class ChatbotStartSessionSerializer(serializers.Serializer):
    """Serializer for starting AI chatbot session"""
    chatbot_type = serializers.ChoiceField(
        choices=[
            ('HYBRID', 'Hybrid Assistant'),
            ('LISTENER', 'Empathetic Listener'),
            ('PRACTICAL_ADVISOR', 'Practical Advisor')
        ]
    )
    initial_message = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional initial message to start the conversation"
    )
    
    def validate_chatbot_type(self, value):
        """Validate chatbot type is supported"""
        from django.conf import settings
        
        valid_types = list(settings.AI_CHATBOT_MODELS.keys())
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid chatbot type. Must be one of: {', '.join(valid_types)}"
            )
        return value


class AIResponseSerializer(serializers.Serializer):
    """Serializer for AI response data"""
    content = serializers.CharField()
    model_used = serializers.CharField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    response_time_ms = serializers.IntegerField()
    crisis_analysis = serializers.DictField(required=False)
    personality_traits_applied = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class ConversationHistorySerializer(serializers.Serializer):
    """Serializer for conversation history context"""
    content = serializers.CharField()
    message_type = serializers.CharField()
    created_at = serializers.DateTimeField()
    sender_type = serializers.CharField()


class ChatbotAnalyticsSerializer(serializers.Serializer):
    """Serializer for AI chatbot analytics"""
    session_id = serializers.UUIDField()
    chatbot_type = serializers.CharField()
    total_interactions = serializers.IntegerField()
    conversation_duration_minutes = serializers.IntegerField()
    sentiment_analysis = serializers.DictField()
    crisis_indicators = serializers.DictField()
    user_satisfaction_predicted = serializers.FloatField()
    topics_covered = serializers.ListField(child=serializers.CharField())
    intervention_suggested = serializers.BooleanField()


class ChatSessionSummarySerializer(serializers.Serializer):
    """Serializer for AI-generated session summary"""
    session_id = serializers.UUIDField()
    summary = serializers.CharField()
    key_topics = serializers.ListField(child=serializers.CharField())
    emotional_journey = serializers.DictField()
    recommendations = serializers.ListField(child=serializers.CharField())
    follow_up_suggestions = serializers.ListField(child=serializers.CharField())
    crisis_assessment = serializers.DictField()
    generated_at = serializers.DateTimeField()