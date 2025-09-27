from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class CrisisType(models.Model):
    """
    Different types of mental health crises
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    severity_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Default severity level (1-10)"
    )
    
    # Keywords and indicators
    trigger_keywords = models.JSONField(default=list, help_text="Keywords that trigger this crisis type")
    behavioral_indicators = models.JSONField(default=list, help_text="Behavioral signs")
    emotional_indicators = models.JSONField(default=list, help_text="Emotional signs")
    
    # Response protocols
    immediate_response = models.TextField(help_text="Immediate response protocol")
    escalation_criteria = models.TextField(help_text="When to escalate")
    
    # Configuration
    is_active = models.BooleanField(default=True)
    requires_immediate_intervention = models.BooleanField(default=False)
    auto_escalate = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-severity_level', 'name']
    
    def __str__(self):
        return f"{self.name} (Level {self.severity_level})"


class CrisisAlert(models.Model):
    """
    Crisis alerts triggered by AI or manual reporting
    """
    class AlertStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        ACKNOWLEDGED = 'acknowledged', _('Acknowledged')
        IN_PROGRESS = 'in_progress', _('In Progress')
        RESOLVED = 'resolved', _('Resolved')
        FALSE_POSITIVE = 'false_positive', _('False Positive')
        ESCALATED = 'escalated', _('Escalated')
    
    class AlertSource(models.TextChoices):
        AI_DETECTION = 'ai_detection', _('AI Detection')
        SELF_REPORT = 'self_report', _('Self Report')
        PEER_REPORT = 'peer_report', _('Peer Report')
        COUNSELOR_ASSESSMENT = 'counselor_assessment', _('Counselor Assessment')
        ASSESSMENT_RESULT = 'assessment_result', _('Assessment Result')
        SYSTEM_TRIGGER = 'system_trigger', _('System Trigger')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crisis_alerts')
    crisis_type = models.ForeignKey(CrisisType, on_delete=models.PROTECT)
    
    # Alert details
    status = models.CharField(max_length=20, choices=AlertStatus.choices, default=AlertStatus.ACTIVE)
    source = models.CharField(max_length=30, choices=AlertSource.choices)
    severity_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="AI confidence in crisis detection"
    )
    
    # Content and context
    description = models.TextField()
    detected_keywords = models.JSONField(default=list, blank=True)
    context_data = models.JSONField(default=dict, blank=True)
    
    # Source references
    chat_session = models.ForeignKey(
        'chat.ChatSession', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='crisis_alerts'
    )
    message = models.ForeignKey(
        'chat.Message', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='crisis_alerts'
    )
    # Removed assessment field since assessments app was removed
    
    # Response tracking
    assigned_counselor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_crisis_alerts',
        limit_choices_to={'role': 'counselor'}
    )
    response_time = models.DurationField(null=True, blank=True)
    resolution_time = models.DurationField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=True)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-severity_level', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['severity_level', 'status']),
            models.Index(fields=['assigned_counselor', 'status']),
            models.Index(fields=['source']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Crisis Alert: {self.user.get_full_name()} - {self.crisis_type.name} (Level {self.severity_level})"


class CrisisResponse(models.Model):
    """
    Actions taken in response to a crisis alert
    """
    class ResponseType(models.TextChoices):
        IMMEDIATE_CONTACT = 'immediate_contact', _('Immediate Contact')
        SAFETY_PLAN = 'safety_plan', _('Safety Plan Activation')
        EMERGENCY_SERVICES = 'emergency_services', _('Emergency Services')
        COUNSELOR_ASSIGNMENT = 'counselor_assignment', _('Counselor Assignment')
        RESOURCE_PROVISION = 'resource_provision', _('Resource Provision')
        FOLLOW_UP_SCHEDULE = 'follow_up_schedule', _('Follow-up Schedule')
        ESCALATION = 'escalation', _('Escalation')
        MONITORING = 'monitoring', _('Increased Monitoring')
    
    alert = models.ForeignKey(CrisisAlert, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crisis_responses')
    
    # Response details
    response_type = models.CharField(max_length=30, choices=ResponseType.choices)
    description = models.TextField()
    actions_taken = models.JSONField(default=list, blank=True)
    
    # Outcome and effectiveness
    was_effective = models.BooleanField(null=True, blank=True)
    user_response = models.TextField(blank=True, help_text="How the user responded")
    next_steps = models.TextField(blank=True)
    
    # Resources and contacts
    resources_provided = models.JSONField(default=list, blank=True)
    contacts_made = models.JSONField(default=list, blank=True)
    
    # Metadata
    response_time = models.DurationField(help_text="Time from alert to response")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert', 'response_type']),
            models.Index(fields=['responder']),
        ]
    
    def __str__(self):
        return f"Response to {self.alert.id}: {self.get_response_type_display()}"


class SafetyPlan(models.Model):
    """
    Personalized safety plans for users
    """
    class PlanStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ACTIVE = 'active', _('Active')
        REVIEW_NEEDED = 'review_needed', _('Review Needed')
        ARCHIVED = 'archived', _('Archived')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='safety_plans')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_safety_plans',
        help_text="Counselor or admin who created this plan"
    )
    
    # Plan details
    title = models.CharField(max_length=200, default="My Safety Plan")
    status = models.CharField(max_length=20, choices=PlanStatus.choices, default=PlanStatus.DRAFT)
    
    # Warning signs and triggers
    warning_signs = models.JSONField(default=list, help_text="Early warning signs")
    triggers = models.JSONField(default=list, help_text="Known triggers")
    
    # Coping strategies
    coping_strategies = models.JSONField(default=list, help_text="Self-help coping strategies")
    safe_spaces = models.JSONField(default=list, help_text="Safe places to go")
    
    # Support contacts
    support_contacts = models.JSONField(default=list, help_text="Friends/family to contact")
    professional_contacts = models.JSONField(default=list, help_text="Mental health professionals")
    crisis_hotlines = models.JSONField(default=list, help_text="Crisis hotline numbers")
    
    # Safety measures
    lethal_means_restriction = models.TextField(blank=True, help_text="Ways to restrict access to harmful items")
    environmental_safety = models.TextField(blank=True, help_text="Making environment safer")
    
    # Emergency procedures
    emergency_procedures = models.TextField(help_text="Step-by-step emergency procedures")
    when_to_call_911 = models.TextField(help_text="Specific criteria for calling emergency services")
    
    # Metadata
    last_reviewed = models.DateTimeField(null=True, blank=True)
    review_frequency_days = models.PositiveIntegerField(default=90)
    times_activated = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Safety Plan: {self.user.get_full_name()} - {self.title}"
    
    def needs_review(self):
        """Check if safety plan needs review"""
        if not self.last_reviewed:
            return True
        
        review_due = self.last_reviewed + timezone.timedelta(days=self.review_frequency_days)
        return timezone.now() > review_due


class CrisisResource(models.Model):
    """
    Resources available during crisis situations
    """
    class ResourceType(models.TextChoices):
        HOTLINE = 'hotline', _('Crisis Hotline')
        EMERGENCY_SERVICE = 'emergency_service', _('Emergency Service')
        ONLINE_CHAT = 'online_chat', _('Online Chat Support')
        TEXT_SERVICE = 'text_service', _('Text/SMS Service')
        MOBILE_APP = 'mobile_app', _('Mobile App')
        WEBSITE = 'website', _('Website Resource')
        LOCAL_SERVICE = 'local_service', _('Local Service')
        SELF_HELP_TOOL = 'self_help_tool', _('Self-Help Tool')
    
    class Availability(models.TextChoices):
        ALWAYS = '24/7', _('24/7 Available')
        BUSINESS_HOURS = 'business', _('Business Hours')
        EVENINGS = 'evenings', _('Evenings/Weekends')
        LIMITED = 'limited', _('Limited Hours')
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    
    # Contact information
    phone_number = models.CharField(max_length=20, blank=True)
    text_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website_url = models.URLField(blank=True)
    chat_url = models.URLField(blank=True)
    
    # Availability and location
    availability = models.CharField(max_length=20, choices=Availability.choices)
    availability_details = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    serves_areas = models.JSONField(default=list, blank=True)
    
    # Targeting and filters
    target_demographics = models.JSONField(default=list, blank=True)
    crisis_types = models.ManyToManyField(CrisisType, blank=True)
    languages_supported = models.JSONField(default=list, blank=True)
    
    # Quality and verification
    is_verified = models.BooleanField(default=False)
    is_free = models.BooleanField(default=True)
    requires_insurance = models.BooleanField(default=False)
    
    # Usage tracking
    click_count = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-is_featured', 'name']
        indexes = [
            models.Index(fields=['resource_type', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['availability']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_resource_type_display()})"


class CrisisFollowUp(models.Model):
    """
    Follow-up actions and check-ins after crisis response
    """
    class FollowUpType(models.TextChoices):
        CHECK_IN = 'check_in', _('Wellness Check-in')
        ASSESSMENT = 'assessment', _('Follow-up Assessment')
        APPOINTMENT = 'appointment', _('Scheduled Appointment')
        SAFETY_PLAN_REVIEW = 'safety_plan_review', _('Safety Plan Review')
        RESOURCE_CHECK = 'resource_check', _('Resource Effectiveness Check')
    
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', _('Scheduled')
        COMPLETED = 'completed', _('Completed')
        MISSED = 'missed', _('Missed')
        CANCELLED = 'cancelled', _('Cancelled')
        RESCHEDULED = 'rescheduled', _('Rescheduled')
    
    alert = models.ForeignKey(CrisisAlert, on_delete=models.CASCADE, related_name='follow_ups')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_follow_ups',
        limit_choices_to={'role__in': ['counselor', 'admin']}
    )
    
    # Follow-up details
    follow_up_type = models.CharField(max_length=30, choices=FollowUpType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    scheduled_date = models.DateTimeField()
    
    # Content
    purpose = models.TextField()
    notes = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    
    # Results
    user_status = models.CharField(max_length=100, blank=True)
    additional_support_needed = models.BooleanField(default=False)
    new_concerns = models.TextField(blank=True)
    
    # Next steps
    next_follow_up_date = models.DateTimeField(null=True, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['alert']),
        ]
    
    def __str__(self):
        return f"Follow-up: {self.alert.user.get_full_name()} - {self.get_follow_up_type_display()}"


class CrisisAnalytics(models.Model):
    """
    Analytics and reporting for crisis management
    """
    # Time period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Alert statistics
    total_alerts = models.PositiveIntegerField(default=0)
    high_severity_alerts = models.PositiveIntegerField(default=0)
    false_positives = models.PositiveIntegerField(default=0)
    ai_detected_alerts = models.PositiveIntegerField(default=0)
    
    # Response statistics
    average_response_time = models.DurationField(null=True, blank=True)
    average_resolution_time = models.DurationField(null=True, blank=True)
    escalation_rate = models.FloatField(default=0.0)
    
    # Outcome statistics
    successful_interventions = models.PositiveIntegerField(default=0)
    follow_up_completion_rate = models.FloatField(default=0.0)
    
    # Trend analysis
    crisis_types_breakdown = models.JSONField(default=dict, blank=True)
    peak_hours = models.JSONField(default=list, blank=True)
    demographic_breakdown = models.JSONField(default=dict, blank=True)
    
    # AI performance
    ai_accuracy_rate = models.FloatField(default=0.0)
    ai_precision = models.FloatField(default=0.0)
    ai_recall = models.FloatField(default=0.0)
    
    # Recommendations
    system_recommendations = models.JSONField(default=list, blank=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-generated_at']
        unique_together = ['start_date', 'end_date']
    
    def __str__(self):
        return f"Crisis Analytics: {self.start_date} to {self.end_date}"
