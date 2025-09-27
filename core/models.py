from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()


class SystemConfiguration(models.Model):
    """
    Global system configuration and settings
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON Object'),
            ('list', 'List'),
        ],
        default='string'
    )
    
    # Access control
    is_public = models.BooleanField(default=False, help_text="Can be accessed by non-admin users")
    is_editable = models.BooleanField(default=True)
    
    # Metadata
    category = models.CharField(max_length=50, blank=True, help_text="Configuration category")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        limit_choices_to={'role': 'admin'}
    )
    
    class Meta:
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_public']),
        ]
    
    def get_value(self):
        """Return the value in the correct data type"""
        if self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'json':
            return json.loads(self.value)
        elif self.data_type == 'list':
            return json.loads(self.value) if self.value else []
        return self.value
    
    def __str__(self):
        return f"{self.key}: {self.value}"


class AuditLog(models.Model):
    """
    System-wide audit logging for important actions
    """
    class ActionType(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        ACCESS = 'access', _('Access')
        EXPORT = 'export', _('Export')
        IMPORT = 'import', _('Import')
        ADMIN_ACTION = 'admin_action', _('Admin Action')
        CRISIS_ACTION = 'crisis_action', _('Crisis Action')
        MODERATION = 'moderation', _('Moderation')
    
    # Actor and action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    action_description = models.TextField()
    
    # Context
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    
    # Additional data
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Status and outcome
    was_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        user_str = self.user.get_full_name() if self.user else "System"
        return f"{user_str} - {self.get_action_type_display()}: {self.action_description}"


class Notification(models.Model):
    """
    System-wide notifications
    """
    class NotificationType(models.TextChoices):
        SYSTEM = 'system', _('System Notification')
        APPOINTMENT = 'appointment', _('Appointment Related')
        ASSESSMENT = 'assessment', _('Assessment Related')
        WELLNESS = 'wellness', _('Wellness Related')
        COMMUNITY = 'community', _('Community Related')
        CRISIS = 'crisis', _('Crisis Alert')
        REMINDER = 'reminder', _('Reminder')
        ACHIEVEMENT = 'achievement', _('Achievement')
        SECURITY = 'security', _('Security Alert')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_notifications'
    )
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Metadata
    action_url = models.URLField(blank=True, help_text="URL to redirect when notification is clicked")
    action_data = models.JSONField(default=dict, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery
    send_email = models.BooleanField(default=False)
    send_push = models.BooleanField(default=True)
    email_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    # Related objects (generic)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True, help_text="Schedule notification for future delivery")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['scheduled_for']),
        ]
    
    def __str__(self):
        return f"Notification for {self.recipient.get_full_name()}: {self.title}"


class FAQ(models.Model):
    """
    Frequently Asked Questions
    """
    class Category(models.TextChoices):
        GENERAL = 'general', _('General')
        ACCOUNT = 'account', _('Account & Profile')
        APPOINTMENTS = 'appointments', _('Appointments')
        ASSESSMENTS = 'assessments', _('Assessments')
        WELLNESS = 'wellness', _('Wellness Tracking')
        COMMUNITY = 'community', _('Community')
        CRISIS = 'crisis', _('Crisis Support')
        PRIVACY = 'privacy', _('Privacy & Security')
        TECHNICAL = 'technical', _('Technical Support')
    
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    
    # Organization
    order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Metadata
    search_keywords = models.JSONField(default=list, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)
    
    # Management
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['admin', 'counselor']}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'question']
        indexes = [
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['is_featured', 'is_published']),
        ]
    
    def __str__(self):
        return f"FAQ: {self.question[:100]}..."


class ContactMessage(models.Model):
    """
    Contact form submissions and support requests
    """
    class MessageType(models.TextChoices):
        GENERAL_INQUIRY = 'general', _('General Inquiry')
        TECHNICAL_SUPPORT = 'tech_support', _('Technical Support')
        FEATURE_REQUEST = 'feature_request', _('Feature Request')
        BUG_REPORT = 'bug_report', _('Bug Report')
        FEEDBACK = 'feedback', _('Feedback')
        COMPLAINT = 'complaint', _('Complaint')
        EMERGENCY = 'emergency', _('Emergency')
    
    class Status(models.TextChoices):
        NEW = 'new', _('New')
        IN_PROGRESS = 'in_progress', _('In Progress')
        RESOLVED = 'resolved', _('Resolved')
        CLOSED = 'closed', _('Closed')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    # Sender info
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    sender_name = models.CharField(max_length=200, blank=True)
    sender_email = models.EmailField(blank=True)
    sender_phone = models.CharField(max_length=20, blank=True)
    
    # Message details
    message_type = models.CharField(max_length=20, choices=MessageType.choices)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    
    # Status and handling
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_messages',
        limit_choices_to={'role__in': ['admin', 'counselor']}
    )
    
    # Response
    response = models.TextField(blank=True)
    response_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['message_type']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        sender_name = self.sender.get_full_name() if self.sender else self.sender_name
        return f"Contact: {sender_name} - {self.subject}"


class SystemAlert(models.Model):
    """
    System-wide alerts and announcements
    """
    class AlertType(models.TextChoices):
        MAINTENANCE = 'maintenance', _('Maintenance')
        OUTAGE = 'outage', _('System Outage')
        UPDATE = 'update', _('System Update')
        SECURITY = 'security', _('Security Alert')
        ANNOUNCEMENT = 'announcement', _('Announcement')
        WARNING = 'warning', _('Warning')
        INFO = 'info', _('Information')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        SCHEDULED = 'scheduled', _('Scheduled')
        RESOLVED = 'resolved', _('Resolved')
        CANCELLED = 'cancelled', _('Cancelled')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Targeting
    target_roles = models.JSONField(default=list, blank=True, help_text="Empty list means all users")
    target_users = models.ManyToManyField(User, blank=True, related_name='targeted_alerts')
    
    # Display options
    is_dismissible = models.BooleanField(default=True)
    show_on_login = models.BooleanField(default=False)
    show_on_dashboard = models.BooleanField(default=True)
    
    # Scheduling
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Management
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['alert_type']),
        ]
    
    def __str__(self):
        return f"System Alert: {self.title}"


class UserPreference(models.Model):
    """
    User-specific preferences and settings
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Specific notification types
    appointment_reminders = models.BooleanField(default=True)
    wellness_reminders = models.BooleanField(default=True)
    community_notifications = models.BooleanField(default=True)
    assessment_reminders = models.BooleanField(default=True)
    crisis_alerts = models.BooleanField(default=True)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('community', 'Community Only'),
            ('private', 'Private'),
        ],
        default='community'
    )
    show_online_status = models.BooleanField(default=True)
    allow_direct_messages = models.BooleanField(default=True)
    
    # Interface preferences
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('auto', 'Auto'),
        ],
        default='auto'
    )
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Dashboard preferences
    dashboard_widgets = models.JSONField(
        default=list,
        blank=True,
        help_text="Enabled dashboard widgets"
    )
    dashboard_layout = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dashboard widget layout"
    )
    
    # Data and privacy
    data_sharing_analytics = models.BooleanField(default=True)
    data_sharing_research = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Preferences for {self.user.get_full_name()}"


class Analytics(models.Model):
    """
    System analytics and metrics tracking
    """
    class MetricType(models.TextChoices):
        USER_ACTIVITY = 'user_activity', _('User Activity')
        FEATURE_USAGE = 'feature_usage', _('Feature Usage')
        PERFORMANCE = 'performance', _('Performance')
        ENGAGEMENT = 'engagement', _('Engagement')
        HEALTH_METRICS = 'health_metrics', _('Health Metrics')
        SYSTEM_METRICS = 'system_metrics', _('System Metrics')
    
    # Metric identification
    metric_type = models.CharField(max_length=20, choices=MetricType.choices)
    metric_name = models.CharField(max_length=100)
    metric_key = models.CharField(max_length=150, help_text="Unique identifier for this metric")
    
    # Data
    value = models.DecimalField(max_digits=15, decimal_places=4)
    unit = models.CharField(max_length=50, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Context
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Aggregation
    period = models.CharField(
        max_length=20,
        choices=[
            ('instant', 'Instant'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='instant'
    )
    period_start = models.DateTimeField(null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_type', 'metric_name']),
            models.Index(fields=['metric_key', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['period', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"
