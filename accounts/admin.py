from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, StudentProfile, CounselorProfile, AdminProfile, UserSession


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Custom User Admin with role-based organization"""
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')}),
        (_('Role & Status'), {'fields': ('role', 'is_verified', 'profile_completed')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Security'), {'fields': ('last_login_ip',), 'classes': ('collapse',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Student Profile Admin"""
    
    list_display = ('user', 'student_id', 'institution', 'course', 'year_of_study', 'created_at')
    list_filter = ('institution', 'year_of_study', 'profile_visibility', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'student_id', 'institution')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Academic Information'), {'fields': ('student_id', 'institution', 'course', 'year_of_study')}),
        (_('Emergency Contact'), {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'),
            'classes': ('collapse',)
        }),
        (_('Preferences'), {
            'fields': ('preferred_language', 'timezone', 'profile_visibility'),
        }),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(CounselorProfile)
class CounselorProfileAdmin(admin.ModelAdmin):
    """Counselor Profile Admin"""
    
    list_display = ('user', 'license_number', 'experience_years', 'is_available', 'is_verified', 'average_rating')
    list_filter = ('is_available', 'is_verified', 'experience_years', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'license_number')
    readonly_fields = ('created_at', 'updated_at', 'average_rating', 'total_reviews')
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Professional Information'), {
            'fields': ('license_number', 'qualifications', 'experience_years', 'specializations')
        }),
        (_('Availability'), {
            'fields': ('is_available', 'working_hours', 'max_daily_appointments', 'session_duration')
        }),
        (_('Verification'), {
            'fields': ('is_verified', 'verification_documents'),
            'classes': ('collapse',)
        }),
        (_('Rating & Reviews'), {
            'fields': ('average_rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('languages_spoken',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    """Admin Profile Admin"""
    
    list_display = ('user', 'department', 'access_level', 'can_manage_users', 'can_handle_crisis', 'login_count')
    list_filter = ('access_level', 'can_manage_users', 'can_manage_content', 'can_handle_crisis', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'department')
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'login_count')
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Admin Information'), {'fields': ('department', 'access_level')}),
        (_('Permissions'), {
            'fields': ('can_manage_users', 'can_manage_content', 'can_view_analytics', 'can_handle_crisis')
        }),
        (_('Activity'), {
            'fields': ('last_login', 'login_count'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User Session Admin for security monitoring"""
    
    list_display = ('user', 'ip_address', 'login_method', 'is_active', 'created_at', 'expires_at')
    list_filter = ('login_method', 'is_active', 'created_at')
    search_fields = ('user__email', 'ip_address', 'user_agent')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Session Info'), {'fields': ('session_key', 'ip_address', 'user_agent', 'location')}),
        (_('Status'), {'fields': ('is_active', 'login_method')}),
        (_('Timestamps'), {'fields': ('created_at', 'last_activity', 'expires_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        return False  # Sessions are created programmatically
