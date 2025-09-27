from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from datetime import timedelta

User = get_user_model()


class AppointmentType(models.Model):
    """
    Different types of counseling appointments
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField(default=60)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True)
    
    # Booking rules
    advance_booking_days = models.PositiveIntegerField(default=7, help_text="How many days in advance can be booked")
    cancellation_hours = models.PositiveIntegerField(default=24, help_text="Hours before appointment for free cancellation")
    max_sessions_per_week = models.PositiveIntegerField(default=3)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.duration_minutes}min)"


class CounselorAvailability(models.Model):
    """
    Counselor's availability schedule
    """
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, _('Monday')
        TUESDAY = 2, _('Tuesday')
        WEDNESDAY = 3, _('Wednesday')
        THURSDAY = 4, _('Thursday')
        FRIDAY = 5, _('Friday')
        SATURDAY = 6, _('Saturday')
        SUNDAY = 7, _('Sunday')
    
    counselor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='availability_schedule',
        limit_choices_to={'role': 'counselor'}
    )
    
    # Schedule details
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Configuration
    is_active = models.BooleanField(default=True)
    appointment_types = models.ManyToManyField(AppointmentType, blank=True)
    
    # Override for specific dates
    specific_date = models.DateField(null=True, blank=True, help_text="Override for specific date")
    is_available = models.BooleanField(default=True, help_text="Available or blocked for this time slot")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['counselor', 'day_of_week', 'start_time']
        unique_together = ['counselor', 'day_of_week', 'start_time', 'specific_date']
        indexes = [
            models.Index(fields=['counselor', 'day_of_week']),
            models.Index(fields=['specific_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        day_name = self.get_day_of_week_display()
        if self.specific_date:
            return f"{self.counselor.get_full_name()} - {self.specific_date} {self.start_time}-{self.end_time}"
        return f"{self.counselor.get_full_name()} - {day_name} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    """
    Individual appointment bookings
    """
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending Confirmation')
        CONFIRMED = 'confirmed', _('Confirmed')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED_BY_STUDENT = 'cancelled_student', _('Cancelled by Student')
        CANCELLED_BY_COUNSELOR = 'cancelled_counselor', _('Cancelled by Counselor')
        NO_SHOW = 'no_show', _('No Show')
        RESCHEDULED = 'rescheduled', _('Rescheduled')
    
    class MeetingType(models.TextChoices):
        IN_PERSON = 'in_person', _('In Person')
        VIDEO_CALL = 'video_call', _('Video Call')
        PHONE_CALL = 'phone_call', _('Phone Call')
        CHAT_ONLY = 'chat_only', _('Chat Only')
        VOICE_CALL = 'voice_call', _('Voice Call')  # For API-based calling
        
    class CounselorPreference(models.TextChoices):
        NO_PREFERENCE = 'no_preference', _('No Preference')
        SPECIFIC_COUNSELOR = 'specific_counselor', _('Specific Counselor Requested')
        GENDER_PREFERENCE = 'gender_preference', _('Gender Preference')
        SPECIALTY_PREFERENCE = 'specialty_preference', _('Specialty Preference')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_appointments',
        limit_choices_to={'role': 'student'}
    )
    counselor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='counselor_appointments',
        limit_choices_to={'role': 'counselor'}
    )
    # Counselor preference fields
    preferred_counselor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_appointments',
        limit_choices_to={'role': 'counselor'},
        help_text="Student's preferred counselor"
    )
    counselor_preference_type = models.CharField(
        max_length=25, 
        choices=CounselorPreference.choices, 
        default=CounselorPreference.NO_PREFERENCE
    )
    preference_reason = models.TextField(
        blank=True, 
        help_text="Reason for counselor preference"
    )
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.PROTECT)
    
    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    timezone_name = models.CharField(max_length=50, default='UTC')
    
    # Status and progress
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    meeting_type = models.CharField(max_length=20, choices=MeetingType.choices, default=MeetingType.VIDEO_CALL)
    
    # Content
    reason = models.TextField(help_text="Reason for appointment")
    student_notes = models.TextField(blank=True, help_text="Additional notes from student")
    counselor_notes = models.TextField(blank=True, help_text="Counselor's notes")
    
    # Meeting details
    meeting_url = models.URLField(blank=True, help_text="Video call link")
    meeting_room = models.CharField(max_length=100, blank=True, help_text="Physical room or virtual room ID")
    meeting_password = models.CharField(max_length=50, blank=True)
    
    # Calling integration fields
    call_session_id = models.CharField(max_length=100, blank=True, help_text="Third-party call API session ID")
    call_provider = models.CharField(max_length=50, blank=True, help_text="Calling service provider (Twilio, Agora, etc.)")
    student_phone = models.CharField(max_length=20, blank=True, help_text="Student's phone number for calls")
    counselor_phone = models.CharField(max_length=20, blank=True, help_text="Counselor's phone number for calls")
    call_recording_url = models.URLField(blank=True, help_text="Call recording link (if enabled)")
    call_duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Actual call duration")
    call_quality_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Technical call quality rating"
    )
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    emergency_session = models.BooleanField(default=False)
    
    # Ratings and feedback
    student_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    student_feedback = models.TextField(blank=True)
    counselor_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    counselor_feedback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Billing
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, default='free')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['counselor', 'status']),
            models.Index(fields=['scheduled_date', 'scheduled_time']),
            models.Index(fields=['status']),
            models.Index(fields=['emergency_session']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} with {self.counselor.get_full_name()} - {self.scheduled_date} {self.scheduled_time}"
    
    @property
    def scheduled_datetime(self):
        """Combine scheduled date and time"""
        return timezone.datetime.combine(self.scheduled_date, self.scheduled_time)
    
    @property
    def end_datetime(self):
        """Calculate end time based on duration"""
        return self.scheduled_datetime + timedelta(minutes=self.duration_minutes)
    
    def can_cancel(self):
        """Check if appointment can be cancelled without penalty"""
        hours_before = self.appointment_type.cancellation_hours
        cancellation_deadline = self.scheduled_datetime - timedelta(hours=hours_before)
        return timezone.now() < cancellation_deadline
    
    def is_upcoming(self):
        """Check if appointment is in the future"""
        return self.scheduled_datetime > timezone.now()


class AppointmentNote(models.Model):
    """
    Session notes and documentation
    """
    class NoteType(models.TextChoices):
        SESSION_NOTES = 'session_notes', _('Session Notes')
        ASSESSMENT = 'assessment', _('Assessment Notes')
        PROGRESS = 'progress', _('Progress Notes')
        CRISIS = 'crisis', _('Crisis Notes')
        ADMINISTRATIVE = 'administrative', _('Administrative Notes')
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointment_notes')
    
    note_type = models.CharField(max_length=20, choices=NoteType.choices, default=NoteType.SESSION_NOTES)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Privacy and access
    is_confidential = models.BooleanField(default=True)
    visible_to_student = models.BooleanField(default=False)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    referenced_assessments = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['appointment', 'note_type']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Note: {self.appointment} - {self.get_note_type_display()}"


class AppointmentReminder(models.Model):
    """
    Reminders for upcoming appointments
    """
    class ReminderType(models.TextChoices):
        EMAIL = 'email', _('Email')
        SMS = 'sms', _('SMS')
        PUSH = 'push', _('Push Notification')
        IN_APP = 'in_app', _('In-App Notification')
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    
    reminder_type = models.CharField(max_length=20, choices=ReminderType.choices)
    scheduled_for = models.DateTimeField()
    message = models.TextField(blank=True)
    
    # Status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=20, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['appointment', 'recipient']),
            models.Index(fields=['is_sent', 'scheduled_for']),
        ]
    
    def __str__(self):
        return f"Reminder: {self.appointment} - {self.recipient.get_full_name()}"


class CounselorUnavailability(models.Model):
    """
    Periods when counselor is unavailable (vacation, sick leave, etc.)
    """
    class UnavailabilityType(models.TextChoices):
        VACATION = 'vacation', _('Vacation')
        SICK_LEAVE = 'sick_leave', _('Sick Leave')
        TRAINING = 'training', _('Training/Conference')
        PERSONAL = 'personal', _('Personal Time')
        EMERGENCY = 'emergency', _('Emergency')
    
    counselor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='unavailability_periods',
        limit_choices_to={'role': 'counselor'}
    )
    
    unavailability_type = models.CharField(max_length=20, choices=UnavailabilityType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True, help_text="Leave blank for full day")
    end_time = models.TimeField(null=True, blank=True, help_text="Leave blank for full day")
    
    reason = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(default=dict, blank=True)
    
    # Admin fields
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_unavailability',
        limit_choices_to={'role': 'admin'}
    )
    is_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'start_time']
        indexes = [
            models.Index(fields=['counselor', 'start_date', 'end_date']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self):
        if self.start_time:
            return f"{self.counselor.get_full_name()} - {self.start_date} {self.start_time} to {self.end_date} {self.end_time}"
        return f"{self.counselor.get_full_name()} - {self.start_date} to {self.end_date}"


class AppointmentTemplate(models.Model):
    """
    Templates for recurring appointments or common appointment types
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Template configuration
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.CASCADE)
    default_duration = models.PositiveIntegerField()
    default_notes = models.TextField(blank=True)
    
    # Recurrence settings
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(default=dict, blank=True)
    max_occurrences = models.PositiveIntegerField(null=True, blank=True)
    
    # Access control
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Template: {self.name}"
