from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """
    Custom User model with role-based authentication
    Supports: Student, Counselor, Admin roles
    """
    class UserRole(models.TextChoices):
        STUDENT = 'student', _('Student')
        COUNSELOR = 'counselor', _('Counselor')
        ADMIN = 'admin', _('Admin')
    
    # Core fields
    email = models.EmailField(unique=True, help_text=_('Required. Enter a valid email address.'))
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        help_text=_('User role in the system')
    )
    
    # Profile fields
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Status fields
    is_verified = models.BooleanField(default=False, help_text=_('Designates whether this user has verified their email.'))
    profile_completed = models.BooleanField(default=False, help_text=_('Whether user has completed their profile setup'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Override username requirement - use email as primary identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'role']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active', 'role']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email}) - {self.get_role_display()}"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()
    
    @property
    def is_student(self):
        return self.role == self.UserRole.STUDENT
    
    @property
    def is_counselor(self):
        return self.role == self.UserRole.COUNSELOR
    
    @property
    def is_admin(self):
        return self.role == self.UserRole.ADMIN


class StudentProfile(models.Model):
    """Extended profile for students"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    
    # Academic info
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    course = models.CharField(max_length=100, blank=True)
    year_of_study = models.PositiveSmallIntegerField(null=True, blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=17, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private')
        ],
        default='friends'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Student Profile: {self.user.get_full_name()}"


class CounselorProfile(models.Model):
    """Extended profile for counselors"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='counselor_profile')
    
    # Professional info
    license_number = models.CharField(max_length=50, unique=True)
    specializations = models.JSONField(default=list, help_text="List of specialization areas")
    qualifications = models.TextField(blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    
    # Availability
    is_available = models.BooleanField(default=True)
    working_hours = models.JSONField(
        default=dict,
        help_text="Weekly schedule in JSON format"
    )
    max_daily_appointments = models.PositiveSmallIntegerField(default=8)
    
    # Verification
    is_verified = models.BooleanField(default=False, help_text="Professional verification status")
    verification_documents = models.JSONField(default=list, blank=True)
    
    # Ratings and reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Settings
    session_duration = models.PositiveSmallIntegerField(default=60, help_text="Default session duration in minutes")
    languages_spoken = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['is_available', 'is_verified']),
            models.Index(fields=['average_rating']),
        ]
    
    def __str__(self):
        return f"Counselor: {self.user.get_full_name()} - {self.license_number}"


class AdminProfile(models.Model):
    """Extended profile for admin users"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='admin_profile')
    
    # Admin specific fields
    department = models.CharField(max_length=100, blank=True)
    access_level = models.CharField(
        max_length=20,
        choices=[
            ('super', 'Super Admin'),
            ('manager', 'Manager'),
            ('moderator', 'Moderator'),
            ('support', 'Support Staff')
        ],
        default='support'
    )
    
    # Permissions
    can_manage_users = models.BooleanField(default=False)
    can_manage_content = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=True)
    can_handle_crisis = models.BooleanField(default=False)
    
    # Activity tracking
    last_login = models.DateTimeField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Admin: {self.user.get_full_name()} - {self.get_access_level_display()}"


class UserSession(models.Model):
    """Track user sessions for security and analytics"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Session info
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Security
    login_method = models.CharField(
        max_length=20,
        choices=[
            ('password', 'Password'),
            ('google', 'Google OAuth'),
            ('token', 'API Token')
        ],
        default='password'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} from {self.ip_address}"
