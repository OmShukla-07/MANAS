from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class ChatSession(models.Model):
    """
    Chat session between user and AI or counselor
    """
    class SessionType(models.TextChoices):
        AI_CHAT = 'ai_chat', _('AI Chat')
        COUNSELOR_CHAT = 'counselor_chat', _('Counselor Chat')
        GROUP_CHAT = 'group_chat', _('Group Chat')
    
    class SessionStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        ENDED = 'ended', _('Ended')
        PAUSED = 'paused', _('Paused')
        CRISIS_ESCALATED = 'crisis_escalated', _('Crisis Escalated')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    counselor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='counselor_sessions',
        limit_choices_to={'role': 'counselor'}
    )
    
    # Session details
    session_type = models.CharField(max_length=20, choices=SessionType.choices, default=SessionType.AI_CHAT)
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.ACTIVE)
    title = models.CharField(max_length=200, blank=True, help_text="Session title/topic")
    
    # Crisis tracking
    crisis_level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Crisis level from 0 (normal) to 10 (severe crisis)"
    )
    crisis_keywords_detected = models.JSONField(default=list, blank=True)
    requires_intervention = models.BooleanField(default=False)
    
    # Session metadata
    language = models.CharField(max_length=10, default='en')
    emotion_analysis = models.JSONField(default=dict, blank=True, help_text="AI emotion analysis results")
    session_summary = models.TextField(blank=True, help_text="AI-generated session summary")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Ratings and feedback
    user_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    user_feedback = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['counselor', 'status']),
            models.Index(fields=['session_type', 'status']),
            models.Index(fields=['crisis_level']),
            models.Index(fields=['requires_intervention']),
        ]
    
    def __str__(self):
        if self.counselor:
            return f"Session: {self.user.get_full_name()} & {self.counselor.get_full_name()}"
        return f"AI Session: {self.user.get_full_name()} - {self.session_type}"
    
    def get_duration(self):
        """Calculate session duration"""
        if self.ended_at:
            return self.ended_at - self.started_at
        return None


class Message(models.Model):
    """
    Individual messages within a chat session
    """
    class MessageType(models.TextChoices):
        USER = 'user', _('User Message')
        AI = 'ai', _('AI Response')
        COUNSELOR = 'counselor', _('Counselor Message')
        SYSTEM = 'system', _('System Message')
    
    class MessageStatus(models.TextChoices):
        SENT = 'sent', _('Sent')
        DELIVERED = 'delivered', _('Delivered')
        READ = 'read', _('Read')
        FAILED = 'failed', _('Failed')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    # Message content
    content = models.TextField(help_text="Message content")
    message_type = models.CharField(max_length=20, choices=MessageType.choices)
    status = models.CharField(max_length=20, choices=MessageStatus.choices, default=MessageStatus.SENT)
    
    # AI specific fields
    ai_model_used = models.CharField(max_length=50, blank=True, help_text="AI model used for response")
    ai_confidence = models.FloatField(null=True, blank=True, help_text="AI confidence score")
    ai_prompt_tokens = models.IntegerField(null=True, blank=True)
    ai_completion_tokens = models.IntegerField(null=True, blank=True)
    
    # Message analysis
    sentiment_score = models.FloatField(null=True, blank=True, help_text="Sentiment analysis score")
    emotion_detected = models.CharField(max_length=50, blank=True)
    crisis_indicators = models.JSONField(default=list, blank=True)
    contains_crisis_keywords = models.BooleanField(default=False)
    
    # Message metadata
    translated_content = models.JSONField(default=dict, blank=True, help_text="Translations in different languages")
    attachments = models.JSONField(default=list, blank=True, help_text="File attachments metadata")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['message_type']),
            models.Index(fields=['contains_crisis_keywords']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.get_message_type_display()}: {content_preview}"


class AIPersonality(models.Model):
    """
    Different AI personalities/characters for chat
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    personality_prompt = models.TextField(help_text="System prompt for this AI personality")
    
    # Personality traits
    specialization = models.CharField(max_length=100, blank=True, help_text="What this AI specializes in")
    tone = models.CharField(max_length=50, default='supportive', help_text="Communication tone")
    response_style = models.CharField(max_length=50, default='conversational')
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_crisis_capable = models.BooleanField(default=False, help_text="Can handle crisis situations")
    max_conversation_length = models.IntegerField(default=50, help_text="Max messages in conversation")
    
    # Avatar and appearance
    avatar_url = models.URLField(blank=True)
    color_theme = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    
    # Usage stats
    usage_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"AI Personality: {self.name}"


class ChatTemplate(models.Model):
    """
    Pre-defined conversation templates and quick responses
    """
    class TemplateType(models.TextChoices):
        GREETING = 'greeting', _('Greeting')
        ASSESSMENT = 'assessment', _('Assessment Question')
        CRISIS_RESPONSE = 'crisis_response', _('Crisis Response')
        ENCOURAGEMENT = 'encouragement', _('Encouragement')
        RESOURCE_SUGGESTION = 'resource_suggestion', _('Resource Suggestion')
        CLOSURE = 'closure', _('Session Closure')
    
    title = models.CharField(max_length=200)
    template_type = models.CharField(max_length=30, choices=TemplateType.choices)
    content = models.TextField()
    
    # Usage conditions
    crisis_level_min = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    crisis_level_max = models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(10)])
    target_emotions = models.JSONField(default=list, blank=True, help_text="Target emotions for this template")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')
    usage_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type', 'title']
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
            models.Index(fields=['crisis_level_min', 'crisis_level_max']),
        ]
    
    def __str__(self):
        return f"{self.get_template_type_display()}: {self.title}"


class MessageReaction(models.Model):
    """
    User reactions to messages (like, helpful, etc.)
    """
    class ReactionType(models.TextChoices):
        LIKE = 'like', _('Like')
        HELPFUL = 'helpful', _('Helpful')
        NOT_HELPFUL = 'not_helpful', _('Not Helpful')
        CONCERNING = 'concerning', _('Concerning')
        INAPPROPRIATE = 'inappropriate', _('Inappropriate')
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=ReactionType.choices)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']  # One reaction per user per message
        indexes = [
            models.Index(fields=['message', 'reaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_reaction_type_display()}"


class ChatAnalytics(models.Model):
    """
    Analytics and insights from chat sessions
    """
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name='analytics')
    
    # Conversation metrics
    total_messages = models.PositiveIntegerField(default=0)
    user_message_count = models.PositiveIntegerField(default=0)
    ai_response_count = models.PositiveIntegerField(default=0)
    average_response_time = models.FloatField(null=True, blank=True, help_text="Average AI response time in seconds")
    
    # Sentiment analysis
    overall_sentiment = models.CharField(max_length=20, blank=True)
    sentiment_trend = models.JSONField(default=list, blank=True, help_text="Sentiment progression over time")
    dominant_emotions = models.JSONField(default=list, blank=True)
    
    # Topic analysis
    main_topics = models.JSONField(default=list, blank=True)
    keywords_mentioned = models.JSONField(default=list, blank=True)
    
    # Crisis indicators
    crisis_keywords_count = models.PositiveIntegerField(default=0)
    highest_crisis_level = models.IntegerField(default=0)
    intervention_triggered = models.BooleanField(default=False)
    
    # AI performance
    ai_helpfulness_score = models.FloatField(null=True, blank=True)
    user_satisfaction_predicted = models.FloatField(null=True, blank=True)
    
    # Generated insights
    ai_summary = models.TextField(blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    follow_up_suggested = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for Session: {self.session.id}"
