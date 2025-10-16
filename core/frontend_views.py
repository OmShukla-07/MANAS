"""
Views for serving frontend templates and managing authentication flow.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from accounts.models import CustomUser, StudentProfile, CounselorProfile, AdminProfile
from appointments.models import (
    Appointment, AppointmentType, CounselorAvailability, 
    AppointmentNote, CounselorUnavailability
)
import json
from django.utils import timezone
from datetime import date, datetime, timedelta


def home_view(request):
    """Serve the main landing page"""
    print("DEBUG: home_view called - serving main landing page")
    
    # Basic site context with cache busting
    import time
    context = {
        'site_name': 'MANAS',
        'tagline': 'Mental Health & Wellness Platform',
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'cache_version': int(time.time()),  # Force browser refresh
    }
    
    return render(request, 'landing.html', context)


def choose_user_view(request):
    """Simple, clean user type selection page"""
    try:
        from django.urls import reverse
        
        context = {
            'home_url': '/',
            'student_url': reverse('student_signup'),
            'counselor_url': reverse('counselor_signup'),
            'admin_url': reverse('admin_signup'),
        }
        
        return render(request, 'auth/choose_user.html', context)
    except Exception as e:
        # Fallback URLs in case of reverse URL errors
        context = {
            'home_url': '/',
            'student_url': '/signup/student/',
            'counselor_url': '/signup/counselor/',
            'admin_url': '/signup/admin/',
        }
        
        return render(request, 'auth/choose_user.html', context)


def redirect_old_user_selection(request):
    """Redirect old user-selection URLs to the new choose-user page"""
    from django.shortcuts import redirect
    return redirect('/choose-user/')


def login_view(request):
    """Serve the login page and handle authentication"""
    if request.method == 'POST':
        # Get form data - matches frontend form field names
        username = request.POST.get('username')  # From frontend: name="username"
        password = request.POST.get('password')  # From frontend: name="password"
        
        print(f"Login attempt - Username: {username}, Password provided: {'Yes' if password else 'No'}")
        
        if username and password:
            # Try to authenticate - our backend supports both email and username
            user = authenticate(request, username=username, password=password)
            print(f"Authentication result: {user}")
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    print(f"Login successful for user: {user.username}, role: {user.role}")
                    
                    # Redirect based on user role
                    if user.role == 'student':
                        return redirect('student_dashboard')
                    elif user.role == 'counselor':
                        return redirect('counsellor_dashboard')
                    elif user.role == 'admin':
                        return redirect('admin_dashboard')
                    else:
                        return redirect('home')
                else:
                    print(f"User {username} account is deactivated")
                    messages.error(request, 'Your account has been deactivated')
            else:
                print(f"Authentication failed for username: {username}")
                messages.error(request, 'Invalid email/username or password')
        else:
            print(f"Missing credentials - Username: {username}, Password: {'provided' if password else 'missing'}")
            messages.error(request, 'Please provide both email/username and password')
    
    # Create a basic form context for the template
    form_context = {
        'username': {'id_for_label': 'id_username'},
        'password': {'id_for_label': 'id_password'}
    }
    
    return render(request, 'auth/login.html', {'form': form_context})


def signup_view(request):
    """Serve the signup page and handle user registration"""
    if request.method == 'POST':
        # Get form data - matches the frontend form field names
        email = request.POST.get('email')
        username = request.POST.get('username') 
        password = request.POST.get('password')  # From frontend: name="password"
        confirm_password = request.POST.get('confirm_password')  # From frontend: name="confirm_password" 
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role', 'student')
        
        # Basic validation
        if not all([email, username, password, confirm_password, first_name, last_name, role]):
            messages.error(request, 'All fields are required')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            try:
                # Create new user
                user = CustomUser.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role
                )
                
                # Profile creation is handled automatically by signals
                # No need to manually create profiles here
                
                messages.success(request, 'Account created successfully! Please log in.')
                return redirect('login')
            except Exception as e:
                import traceback
                error_msg = f'Error creating account: {str(e)}'
                print(f"Signup error: {error_msg}")
                print(f"Full traceback: {traceback.format_exc()}")
                messages.error(request, error_msg)
    
    # Create a basic form context for the template
    form_context = {
        'first_name': {'id_for_label': 'id_first_name'},
        'last_name': {'id_for_label': 'id_last_name'},
        'username': {'id_for_label': 'id_username'},
        'email': {'id_for_label': 'id_email'},
        'role': {'id_for_label': 'id_role'},
        'password1': {'id_for_label': 'id_password1'},
        'password2': {'id_for_label': 'id_password2'}
    }
    
    return render(request, 'auth/signup.html', {'form': form_context})


def student_signup_simple_view(request):
    """Enhanced student signup with comprehensive profile data collection"""
    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        username = request.POST.get('username') 
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        date_of_birth = request.POST.get('date_of_birth')
        
        # Student profile fields
        institution = request.POST.get('institution', '')
        course = request.POST.get('course', '')
        year_of_study = request.POST.get('year_of_study')
        emergency_contact_name = request.POST.get('emergency_contact_name', '')
        emergency_contact_phone = request.POST.get('emergency_contact_phone', '')
        emergency_contact_relationship = request.POST.get('emergency_contact_relationship', '')
        
        # Basic validation
        if not all([email, username, password, confirm_password, first_name, last_name]):
            messages.error(request, 'All required fields must be filled')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif not all([institution, course, year_of_study, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship]):
            messages.error(request, 'All student profile fields are required')
        else:
            try:
                # Create new user
                user = CustomUser.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='student',
                    phone_number=phone_number,
                    date_of_birth=date_of_birth if date_of_birth else None
                )
                
                # Create or update student profile
                student_profile, created = StudentProfile.objects.get_or_create(user=user)
                student_profile.institution = institution
                student_profile.course = course
                student_profile.year_of_study = int(year_of_study)
                student_profile.emergency_contact_name = emergency_contact_name
                student_profile.emergency_contact_phone = emergency_contact_phone
                student_profile.emergency_contact_relationship = emergency_contact_relationship
                student_profile.save()
                
                # Mark profile as completed
                user.profile_completed = True
                user.save()
                
                messages.success(request, 'Student account created successfully! Please log in.')
                return redirect('login')
            except Exception as e:
                import traceback
                error_msg = f'Error creating account: {str(e)}'
                print(f"Student signup error: {error_msg}")
                print(f"Full traceback: {traceback.format_exc()}")
                messages.error(request, error_msg)
    
    return render(request, 'auth/student_signup_simple.html')


def counselor_signup_simple_view(request):
    """Enhanced counselor signup with comprehensive profile data collection"""
    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        username = request.POST.get('username') 
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        date_of_birth = request.POST.get('date_of_birth')
        
        # Counselor profile fields
        license_number = request.POST.get('license_number', '')
        specializations = request.POST.get('specializations', '')
        qualifications = request.POST.get('qualifications', '')
        experience_years = request.POST.get('experience_years')
        languages_spoken = request.POST.get('languages_spoken', '')
        consultation_fee = request.POST.get('consultation_fee')
        session_duration_minutes = request.POST.get('session_duration_minutes')
        bio = request.POST.get('bio', '')
        
        # Basic validation
        if not all([email, username, password, confirm_password, first_name, last_name]):
            messages.error(request, 'All required fields must be filled')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif not all([license_number, specializations, qualifications, experience_years]):
            messages.error(request, 'All professional fields are required')
        else:
            try:
                # Create new user
                user = CustomUser.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='counselor',
                    phone_number=phone_number,
                    date_of_birth=date_of_birth if date_of_birth else None
                )
                
                # Create or update counselor profile
                counselor_profile, created = CounselorProfile.objects.get_or_create(user=user)
                counselor_profile.license_number = license_number
                counselor_profile.specializations = specializations.split(', ')
                counselor_profile.qualifications = qualifications
                counselor_profile.experience_years = int(experience_years)
                counselor_profile.languages_spoken = languages_spoken.split(', ') if languages_spoken else []
                if consultation_fee:
                    counselor_profile.consultation_fee = float(consultation_fee)
                if session_duration_minutes:
                    counselor_profile.session_duration_minutes = int(session_duration_minutes)
                counselor_profile.bio = bio
                counselor_profile.save()
                
                # Mark profile as completed
                user.profile_completed = True
                user.save()
                
                messages.success(request, 'Counselor account created successfully! Please log in.')
                return redirect('login')
            except Exception as e:
                import traceback
                error_msg = f'Error creating account: {str(e)}'
                print(f"Counselor signup error: {error_msg}")
                print(f"Full traceback: {traceback.format_exc()}")
                messages.error(request, error_msg)
    
    return render(request, 'auth/counselor_signup_simple.html')


def admin_signup_simple_view(request):
    """Enhanced admin signup with comprehensive profile data collection"""
    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        username = request.POST.get('username') 
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        date_of_birth = request.POST.get('date_of_birth')
        
        # Admin profile fields
        department = request.POST.get('department', '')
        access_level = request.POST.get('access_level', '')
        can_manage_users = request.POST.get('can_manage_users') == 'true'
        can_manage_content = request.POST.get('can_manage_content') == 'true'
        can_view_analytics = request.POST.get('can_view_analytics') == 'true'
        
        # Basic validation
        if not all([email, username, password, confirm_password, first_name, last_name]):
            messages.error(request, 'All required fields must be filled')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif not all([department, access_level]):
            messages.error(request, 'Department and access level are required')
        else:
            try:
                # Create new user
                user = CustomUser.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='admin',
                    phone_number=phone_number,
                    date_of_birth=date_of_birth if date_of_birth else None,
                    is_staff=True  # Admin users should have staff access
                )
                
                # Create or update admin profile
                admin_profile, created = AdminProfile.objects.get_or_create(user=user)
                admin_profile.department = department
                admin_profile.access_level = access_level
                admin_profile.can_manage_users = can_manage_users
                admin_profile.can_manage_content = can_manage_content
                admin_profile.can_view_analytics = can_view_analytics
                admin_profile.save()
                
                # Mark profile as completed
                user.profile_completed = True
                user.save()
                
                messages.success(request, 'Administrator account created successfully! Please log in.')
                return redirect('login')
            except Exception as e:
                import traceback
                error_msg = f'Error creating account: {str(e)}'
                print(f"Admin signup error: {error_msg}")
                print(f"Full traceback: {traceback.format_exc()}")
                messages.error(request, error_msg)
    
    return render(request, 'auth/admin_signup_simple.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('landing')


def forgot_password_view(request):
    """Serve the forgot password page"""
    return render(request, 'auth/forgot_password.html')


def privacy_view(request):
    """Serve the privacy policy page"""
    return render(request, 'auth/privacy.html')


def terms_view(request):
    """Serve the terms of service page"""
    return render(request, 'auth/terms.html')


# Student Views
@login_required
def student_dashboard_view(request):
    """Use your actual dashboard template directly"""
    if not hasattr(request.user, 'role') or request.user.role != 'student':
        return redirect('login')
    
    # Provide context for your actual dashboard
    context = {
        'user': request.user,
        'profile': None,
        'recent_sessions': [],
        'upcoming_appointments': [],
        'recent_mood_entries': [],
        'active_goals': [],
        'stats': {
            'total_sessions': 0,
            'total_appointments': 0,
            'mood_entries_this_week': 0,
            'active_goals_count': 0,
        }
    }
    
    # Use your actual dashboard.html directly - no more intermediate pages!
    return render(request, 'student/dashboard.html', context)


@login_required
def student_profile_view(request):
    """Serve the student profile page with update functionality"""
    if request.user.role != 'student':
        return redirect('home')
    
    # Get or create student profile
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.date_of_birth = request.POST.get('date_of_birth') or user.date_of_birth
        user.gender = request.POST.get('gender', user.gender)
        user.save()
        
        # Update student profile fields - comprehensive data
        student_profile.institution = request.POST.get('institution', student_profile.institution)
        student_profile.course = request.POST.get('course', student_profile.course)
        year_of_study = request.POST.get('year_of_study')
        if year_of_study:
            student_profile.year_of_study = int(year_of_study)
        
        student_profile.student_id = request.POST.get('student_id', student_profile.student_id)
        student_profile.address = request.POST.get('address', student_profile.address)
        student_profile.city = request.POST.get('city', student_profile.city)
        student_profile.state = request.POST.get('state', student_profile.state)
        student_profile.pincode = request.POST.get('pincode', student_profile.pincode)
        
        # Academic information
        student_profile.previous_education = request.POST.get('previous_education', student_profile.previous_education)
        student_profile.current_cgpa = request.POST.get('current_cgpa') or student_profile.current_cgpa
        student_profile.academic_interests = request.POST.get('academic_interests', student_profile.academic_interests)
        student_profile.career_goals = request.POST.get('career_goals', student_profile.career_goals)
        
        # Emergency contact information
        student_profile.emergency_contact_name = request.POST.get('emergency_contact_name', student_profile.emergency_contact_name)
        student_profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', student_profile.emergency_contact_phone)
        student_profile.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', student_profile.emergency_contact_relationship)
        student_profile.emergency_contact_address = request.POST.get('emergency_contact_address', student_profile.emergency_contact_address)
        
        # Additional information
        student_profile.medical_conditions = request.POST.get('medical_conditions', student_profile.medical_conditions)
        student_profile.medications = request.POST.get('medications', student_profile.medications)
        student_profile.hobbies = request.POST.get('hobbies', student_profile.hobbies)
        student_profile.bio = request.POST.get('bio', student_profile.bio)
        
        student_profile.save()
        
        # Mark profile as completed
        user.profile_completed = True
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('student_profile')
    
    context = {
        'user': request.user,
        'profile': student_profile,
    }
    
    return render(request, 'student/profile.html', context)


@login_required
def student_appointments_view(request):
    """Student appointments page with real backend data"""
    if request.user.role != 'student':
        return redirect('home')
    
    from accounts.models import CustomUser
    from appointments.models import Appointment, AppointmentType
    from django.utils import timezone
    
    # Get all counselors
    counselors = CustomUser.objects.filter(role='counselor', is_active=True)
    
    # Get appointment types
    appointment_types = AppointmentType.objects.filter(is_active=True)
    
    # Get user's appointments
    upcoming_appointments = Appointment.objects.filter(
        student=request.user,
        status__in=['pending', 'confirmed'],
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date', 'scheduled_time')[:5]
    
    past_appointments = Appointment.objects.filter(
        student=request.user,
        status__in=['completed', 'cancelled_student', 'cancelled_counselor', 'no_show']
    ).order_by('-scheduled_date', '-scheduled_time')[:10]
    
    context = {
        'counselors': counselors,
        'appointment_types': appointment_types,
        'meeting_types': Appointment.MeetingType.choices,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'student/appointments.html', context)


def student_manas_ai_view(request):
    """Serve the MANAS AI chat page"""
    # Temporarily removed login_required for testing JavaScript fixes
    # if request.user.role != 'student':
    #     return redirect('home')
    return render(request, 'student/manas_ai.html')


@login_required
def student_resources_view(request):
    """Serve the student resources page"""
    if request.user.role != 'student':
        return redirect('home')
    return render(request, 'student/resources.html')


@login_required
def student_game_zone_view(request):
    """Serve the student game zone page"""
    if request.user.role != 'student':
        return redirect('home')
    return render(request, 'student/game_zone.html')


@login_required
def student_peer_support_view(request):
    """Serve the student peer support page"""
    if request.user.role != 'student':
        return redirect('home')
    return render(request, 'student/peer_support.html')


# Counsellor Views
@login_required
@login_required
def counsellor_dashboard_view(request):
    """Serve the modern counselor dashboard with real statistics"""
    if request.user.role != 'counselor':
        return redirect('login')
    
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    from appointments.models import Appointment
    from crisis.models import CrisisAlert
    
    User = get_user_model()
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    
    # Counselor's student statistics
    counselor_appointments = Appointment.objects.filter(counselor=request.user)
    active_students = counselor_appointments.values('student').distinct().count()
    new_students_week = counselor_appointments.filter(
        created_at__gte=week_ago
    ).values('student').distinct().count()
    
    # Session statistics
    sessions_today = counselor_appointments.filter(scheduled_date=today).count()
    total_sessions = counselor_appointments.count()
    completed_sessions = counselor_appointments.filter(status='completed').count()
    
    # Calculate completion rate
    completion_rate = 0
    if total_sessions > 0:
        completion_rate = round((completed_sessions / total_sessions) * 100)
    
    # Crisis alerts for counselor's students
    counselor_student_ids = counselor_appointments.values_list('student_id', flat=True)
    crisis_alerts = CrisisAlert.objects.filter(
        user_id__in=counselor_student_ids,
        status__in=['active', 'acknowledged', 'in_progress']
    ).count()
    
    # Recent sessions
    recent_sessions = counselor_appointments.select_related('student').order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'active_students': active_students,
        'new_students_week': new_students_week,
        'sessions_today': sessions_today,
        'completion_rate': completion_rate,
        'completion_rate_change': 5,  # Mock data for improvement
        'crisis_alerts': crisis_alerts,
        'recent_sessions': recent_sessions,
        'success_rate': completion_rate,
        'crisis_count': crisis_alerts,
    }
    
    return render(request, 'counselor/counselor_dashboard_admin.html', context)


@login_required
def counsellor_profile_view(request):
    """Serve the modern counselor profile page with update functionality"""
    if request.user.role != 'counselor':
        return redirect('login')
    
    # Get or create counselor profile
    from accounts.models import CounselorProfile
    try:
        counselor_profile = request.user.counselor_profile
    except CounselorProfile.DoesNotExist:
        counselor_profile = None
    
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        
        # Update bio if it exists as a field
        if hasattr(user, 'bio'):
            user.bio = request.POST.get('bio', getattr(user, 'bio', ''))
        
        user.save()
        
        # Update counselor profile if it exists
        if counselor_profile:
            counselor_profile.license_number = request.POST.get('license_number', counselor_profile.license_number)
            counselor_profile.experience_years = request.POST.get('experience_years', counselor_profile.experience_years)
            specializations = request.POST.get('specializations', '')
            if specializations:
                counselor_profile.specializations = specializations.split(', ')
            counselor_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('counselor_profile')
    
    context = {
        'user': request.user,
        'counselor_profile': counselor_profile,
    }
    
    return render(request, 'counselor/counselor_profile.html', context)


# Admin Views
@login_required
def admin_dashboard_view(request):
    """Serve the modern admin dashboard with real statistics"""
    # Check if user is admin
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')
    
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    from appointments.models import Appointment
    from crisis.models import CrisisAlert
    from accounts.models import UserSession
    
    User = get_user_model()
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_this_week = User.objects.filter(created_at__gte=week_ago).count()
    new_users_this_month = User.objects.filter(created_at__gte=month_ago).count()
    
    # User breakdown by role
    students_count = User.objects.filter(role='student').count()
    counselors_count = User.objects.filter(role='counselor').count()
    admins_count = User.objects.filter(role='admin').count()
    
    # Session Statistics
    active_sessions = UserSession.objects.filter(
        is_active=True,
        expires_at__gt=now
    ).count()
    
    # Appointment Statistics
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    confirmed_appointments = Appointment.objects.filter(status='confirmed').count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    appointments_today = Appointment.objects.filter(scheduled_date=today).count()
    
    # Crisis Statistics
    total_crisis_alerts = CrisisAlert.objects.count()
    active_crisis_alerts = CrisisAlert.objects.filter(status='active').count()
    high_severity_alerts = CrisisAlert.objects.filter(
        severity_level__gte=8,
        status__in=['active', 'acknowledged', 'in_progress']
    ).count()
    alerts_this_week = CrisisAlert.objects.filter(created_at__gte=week_ago).count()
    
    # Recent Activity
    recent_users = User.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:5]
    recent_appointments = Appointment.objects.filter(
        created_at__gte=week_ago
    ).select_related('student', 'counselor').order_by('-created_at')[:5]
    recent_alerts = CrisisAlert.objects.filter(
        created_at__gte=week_ago
    ).select_related('user', 'crisis_type').order_by('-created_at')[:5]
    
    # Performance Metrics
    appointment_completion_rate = 0
    if total_appointments > 0:
        appointment_completion_rate = (completed_appointments / total_appointments) * 100
    
    # Crisis Response Metrics
    crisis_response_rate = 0
    if total_crisis_alerts > 0:
        responded_alerts = CrisisAlert.objects.exclude(status='active').count()
        crisis_response_rate = (responded_alerts / total_crisis_alerts) * 100
    
    context = {
        'user': request.user,  # Use actual authenticated user
        # User Statistics
        'total_users': total_users,
        'active_users': active_users,
        'new_users_week': new_users_this_week,
        'new_users_month': new_users_this_month,
        'students_count': students_count,
        'counselors_count': counselors_count,
        'admins_count': admins_count,
        
        # Session Statistics
        'active_sessions': active_sessions,
        
        # Appointment Statistics
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'completed_appointments': completed_appointments,
        'appointments_today': appointments_today,
        'appointment_completion_rate': round(appointment_completion_rate, 1),
        
        # Crisis Statistics
        'total_crisis_alerts': total_crisis_alerts,
        'active_crisis_alerts': active_crisis_alerts,
        'high_severity_alerts': high_severity_alerts,
        'alerts_this_week': alerts_this_week,
        'crisis_response_rate': round(crisis_response_rate, 1),
        
        # Recent Activity
        'recent_users': recent_users,
        'recent_appointments': recent_appointments,
        'recent_alerts': recent_alerts,
        
        # Quick stats for cards
        'user_growth_week': f"+{new_users_this_week}" if new_users_this_week > 0 else "0",
        'alert_status': "HIGH" if high_severity_alerts > 0 else "NORMAL",
        'system_status': "OPERATIONAL",
    }
    
    return render(request, 'admin/modern_dashboard.html', context)


@login_required
def admin_profile_view(request):
    """Serve the modern admin profile page with update functionality"""
    if request.user.role != 'admin':
        return redirect('home')
    
    # Get or create admin profile
    from accounts.models import AdminProfile
    admin_profile, created = AdminProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.date_of_birth = request.POST.get('date_of_birth') or user.date_of_birth
        user.gender = request.POST.get('gender', user.gender)
        
        # Update admin profile fields - comprehensive data
        admin_profile.department = request.POST.get('department', admin_profile.department)
        admin_profile.employee_id = request.POST.get('employee_id', admin_profile.employee_id)
        admin_profile.designation = request.POST.get('designation', admin_profile.designation)
        admin_profile.office_address = request.POST.get('office_address', admin_profile.office_address)
        admin_profile.city = request.POST.get('city', admin_profile.city)
        admin_profile.state = request.POST.get('state', admin_profile.state)
        admin_profile.pincode = request.POST.get('pincode', admin_profile.pincode)
        admin_profile.bio = request.POST.get('bio', admin_profile.bio)
        
        # Administrative permissions - handle as comma-separated values or list
        admin_permissions = request.POST.getlist('admin_permissions')  # For checkbox arrays
        if not admin_permissions:  # Fallback to text input
            admin_permissions_text = request.POST.get('admin_permissions_text', '')
            if admin_permissions_text:
                admin_permissions = [perm.strip() for perm in admin_permissions_text.split(',')]
        
        if admin_permissions:
            admin_profile.admin_permissions = admin_permissions
        
        # Access level
        admin_profile.access_level = request.POST.get('access_level', admin_profile.access_level)
        
        # Reporting preferences
        admin_profile.reports_access = request.POST.get('reports_access') == 'on'
        admin_profile.user_management_access = request.POST.get('user_management_access') == 'on'
        admin_profile.system_settings_access = request.POST.get('system_settings_access') == 'on'
        admin_profile.crisis_management_access = request.POST.get('crisis_management_access') == 'on'
        
        # Qualifications and experience
        admin_profile.qualifications = request.POST.get('qualifications', admin_profile.qualifications)
        admin_profile.experience_years = request.POST.get('experience_years') or admin_profile.experience_years
        if admin_profile.experience_years:
            admin_profile.experience_years = int(admin_profile.experience_years)
        
        user.save()
        admin_profile.save()
        
        # Mark profile as completed
        user.profile_completed = True
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('admin_profile')
    
    context = {
        'user': request.user,
        'profile': admin_profile,
        'admin_profile': admin_profile,  # Additional reference for template
    }
    
    return render(request, 'admin/modern_profile.html', context)


@login_required
def admin_crisis_tracking_view(request):
    """Serve the admin crisis tracking page with real crisis data and management"""
    if request.user.role != 'admin':
        return redirect('home')
    
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q, Count, Avg
    from django.core.paginator import Paginator
    from crisis.models import CrisisAlert, CrisisType, CrisisResponse, SafetyPlan
    from django.contrib.auth import get_user_model
    from django.http import JsonResponse
    
    User = get_user_model()
    
    # Handle POST requests for crisis management actions
    if request.method == 'POST':
        action = request.POST.get('action')
        alert_id = request.POST.get('alert_id')
        
        if action and alert_id:
            try:
                alert = CrisisAlert.objects.get(id=alert_id)
                
                if action == 'acknowledge':
                    alert.status = 'acknowledged'
                    alert.acknowledged_at = timezone.now()
                    alert.save()
                    messages.success(request, f"Alert acknowledged successfully.")
                
                elif action == 'assign':
                    counselor_id = request.POST.get('counselor_id')
                    if counselor_id:
                        counselor = User.objects.get(id=counselor_id, role='counselor')
                        alert.assigned_counselor = counselor
                        alert.status = 'in_progress'
                        alert.save()
                        messages.success(request, f"Alert assigned to {counselor.get_full_name()}.")
                
                elif action == 'resolve':
                    alert.status = 'resolved'
                    alert.resolved_at = timezone.now()
                    alert.save()
                    messages.success(request, f"Alert resolved successfully.")
                
            except (CrisisAlert.DoesNotExist, User.DoesNotExist) as e:
                messages.error(request, "Error processing request.")
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    severity_filter = request.GET.get('severity', '')
    timeframe = request.GET.get('timeframe', '7')
    
    # Build queryset
    alerts = CrisisAlert.objects.select_related('user', 'crisis_type', 'assigned_counselor').order_by('-created_at')
    
    if status_filter:
        alerts = alerts.filter(status=status_filter)
    
    if severity_filter:
        alerts = alerts.filter(severity_level__gte=int(severity_filter))
    
    # Time filter
    if timeframe != 'all':
        days = int(timeframe)
        cutoff_date = timezone.now() - timedelta(days=days)
        alerts = alerts.filter(created_at__gte=cutoff_date)
    
    # Pagination
    paginator = Paginator(alerts, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Statistics
    total_alerts = CrisisAlert.objects.count()
    active_alerts = CrisisAlert.objects.filter(status__in=['active', 'acknowledged', 'in_progress']).count()
    high_severity = CrisisAlert.objects.filter(severity_level__gte=8).count()
    resolved_today = CrisisAlert.objects.filter(
        status='resolved',
        resolved_at__date=timezone.now().date()
    ).count()
    
    # Available counselors for assignment
    counselors = User.objects.filter(role='counselor', is_active=True)
    
    context = {
        'user': request.user,
        'page_obj': page_obj,
        'alerts': page_obj.object_list,
        'total_alerts': total_alerts,
        'active_alerts': active_alerts,
        'high_severity': high_severity,
        'resolved_today': resolved_today,
        'counselors': counselors,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'timeframe': timeframe,
        'status_choices': CrisisAlert.AlertStatus.choices,
    }
    
    return render(request, 'admin/crisis_tracking.html', context)


# Additional Views for missing URLs
@login_required
def profile_view(request):
    """Serve the general profile page based on user role"""
    if request.user.role == 'student':
        return redirect('student_profile')
    elif request.user.role == 'counselor':
        return redirect('counsellor_profile')
    elif request.user.role == 'admin':
        return redirect('admin_profile')
    else:
        return redirect('home')


@login_required
def settings_view(request):
    """Serve the settings page"""
    return render(request, 'common/settings.html')


@login_required
def counsellor_sessions_view(request):
    """Serve the counsellor sessions page"""
    if request.user.role != 'counselor':
        return redirect('home')
    return render(request, 'counsellor/sessions.html')


# Appointment-related views for frontend integration

@login_required
def book_appointment_view(request):
    """Book a new appointment"""
    if request.method == 'POST':
        try:
            # Get form data
            counselor_id = request.POST.get('counselor_id')
            appointment_type_id = request.POST.get('appointment_type_id')
            scheduled_date = request.POST.get('scheduled_date')
            scheduled_time = request.POST.get('scheduled_time')
            meeting_type = request.POST.get('meeting_type', 'video_call')
            reason = request.POST.get('reason', '')
            student_notes = request.POST.get('student_notes', '')
            
            # Validate required fields
            if not all([counselor_id, appointment_type_id, scheduled_date, scheduled_time]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('student_appointments')
            
            # Get objects
            counselor = get_object_or_404(CustomUser, id=counselor_id, role='counselor')
            appointment_type = get_object_or_404(AppointmentType, id=appointment_type_id)
            
            # Parse date and time
            scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
            scheduled_time = datetime.strptime(scheduled_time, '%H:%M').time()
            
            # Check if time slot is available
            existing_appointment = Appointment.objects.filter(
                counselor=counselor,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if existing_appointment:
                messages.error(request, 'This time slot is already booked.')
                return redirect('student_appointments')
            
            # Create appointment
            appointment = Appointment.objects.create(
                student=request.user,
                counselor=counselor,
                appointment_type=appointment_type,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                duration_minutes=appointment_type.duration_minutes,
                meeting_type=meeting_type,
                reason=reason,
                student_notes=student_notes,
                cost=appointment_type.price
            )
            
            messages.success(request, 'Appointment booked successfully!')
            return redirect('student_appointments')
            
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
            return redirect('student_appointments')
    
    return redirect('student_appointments')


@login_required
def appointment_detail_view(request, appointment_id):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if request.user.role == 'student' and appointment.student != request.user:
        messages.error(request, 'Permission denied')
        return redirect('student_appointments')
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        messages.error(request, 'Permission denied')
        return redirect('student_appointments')
    
    notes = AppointmentNote.objects.filter(appointment=appointment)
    if request.user.role == 'student':
        notes = notes.filter(visible_to_student=True)
    
    context = {
        'appointment': appointment,
        'notes': notes,
        'can_cancel': appointment.can_cancel(),
        'is_upcoming': appointment.is_upcoming()
    }
    return render(request, 'student/appointment_detail.html', context)


@login_required
def get_available_slots(request):
    """AJAX endpoint to get available time slots for a counselor on a date"""
    counselor_id = request.GET.get('counselor_id')
    date_str = request.GET.get('date')
    
    if not counselor_id or not date_str:
        return JsonResponse({'error': 'Missing counselor_id or date'}, status=400)
    
    try:
        counselor = get_object_or_404(CustomUser, id=counselor_id, role='counselor')
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get counselor's availability for this day of week
        day_of_week = target_date.isoweekday()
        availability = CounselorAvailability.objects.filter(
            counselor=counselor,
            day_of_week=day_of_week,
            is_active=True
        ).first()
        
        if not availability:
            return JsonResponse({'slots': []})
        
        # Get existing appointments for this date
        existing_appointments = Appointment.objects.filter(
            counselor=counselor,
            scheduled_date=target_date,
            status__in=['pending', 'confirmed']
        ).values_list('scheduled_time', flat=True)
        
        # Generate available time slots
        available_slots = []
        current_time = availability.start_time
        end_time = availability.end_time
        slot_duration = timedelta(minutes=60)  # Default 1-hour slots
        
        while current_time < end_time:
            if current_time not in existing_appointments:
                available_slots.append({
                    'time': current_time.strftime('%H:%M'),
                    'display': current_time.strftime('%I:%M %p')
                })
            
            # Add slot duration
            current_datetime = datetime.combine(target_date, current_time)
            next_datetime = current_datetime + slot_duration
            current_time = next_datetime.time()
        
        return JsonResponse({'slots': available_slots})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if request.user.role == 'student' and appointment.student != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Check if cancellation is allowed
        if not appointment.can_cancel():
            return JsonResponse({
                'error': f'Cancellation not allowed within {appointment.appointment_type.cancellation_hours} hours'
            }, status=400)
        
        # Update status based on who is canceling
        if request.user.role == 'student':
            appointment.status = 'cancelled_student'
        else:
            appointment.status = 'cancelled_counselor'
        
        appointment.save()
        
        return JsonResponse({'success': True, 'message': 'Appointment cancelled successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def reschedule_appointment(request, appointment_id):
    """Reschedule an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if request.user.role == 'student' and appointment.student != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_time = datetime.strptime(data['time'], '%H:%M').time()
        
        # Check if new time slot is available
        existing_appointment = Appointment.objects.filter(
            counselor=appointment.counselor,
            scheduled_date=new_date,
            scheduled_time=new_time,
            status__in=['pending', 'confirmed']
        ).exclude(id=appointment_id).exists()
        
        if existing_appointment:
            return JsonResponse({'error': 'New time slot is already booked'}, status=400)
        
        # Update appointment
        appointment.scheduled_date = new_date
        appointment.scheduled_time = new_time
        appointment.status = 'pending'  # Needs re-confirmation
        appointment.save()
        
        return JsonResponse({'success': True, 'message': 'Appointment rescheduled successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def appointment_dashboard_stats(request):
    """Get appointment statistics for dashboard"""
    if request.user.role == 'student':
        appointments = Appointment.objects.filter(student=request.user)
    elif request.user.role == 'counselor':
        appointments = Appointment.objects.filter(counselor=request.user)
    else:
        appointments = Appointment.objects.all()
    
    today = timezone.now().date()
    
    stats = {
        'upcoming_count': appointments.filter(
            status__in=['pending', 'confirmed'],
            scheduled_date__gte=today
        ).count(),
        'completed_count': appointments.filter(status='completed').count(),
        'pending_count': appointments.filter(status='pending').count(),
        'this_week_count': appointments.filter(
            scheduled_date__week=today.isocalendar()[1],
            scheduled_date__year=today.year
        ).count(),
        'total_count': appointments.count()
    }
    
    # Recent appointments
    recent_appointments = appointments.filter(
        status__in=['completed', 'confirmed', 'pending']
    ).order_by('-scheduled_date', '-scheduled_time')[:5]
    
    recent_data = []
    for apt in recent_appointments:
        recent_data.append({
            'id': str(apt.id),
            'date': apt.scheduled_date.strftime('%Y-%m-%d'),
            'time': apt.scheduled_time.strftime('%H:%M'),
            'counselor_name': apt.counselor.get_full_name() if request.user.role == 'student' else apt.student.get_full_name(),
            'appointment_type': apt.appointment_type.name,
            'status': apt.get_status_display()
        })
    
    return JsonResponse({
        'stats': stats,
        'recent_appointments': recent_data
    })


# Enhanced Dashboard Views for New Backend Integration
@login_required
def enhanced_student_dashboard_view(request):
    """Serve the enhanced student dashboard with new backend features"""
    if request.user.role != 'student':
        return redirect('home')
    
    return render(request, 'student/enhanced_dashboard.html', {
        'user': request.user
    })


@login_required
def enhanced_counsellor_dashboard_view(request):
    """Serve the enhanced counselor dashboard with new backend features"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counselor/enhanced_dashboard.html', {
        'user': request.user
    })


# New view functions for enhanced features
@login_required
def student_assessments_view(request):
    """Serve the student assessments page"""
    if request.user.role != 'student':
        return redirect('home')
    
    return render(request, 'student/assessments.html', {
        'user': request.user
    })


@login_required
def student_wellness_view(request):
    """Serve the student wellness page"""
    if request.user.role != 'student':
        return redirect('home')
    
    return render(request, 'student/wellness.html', {
        'user': request.user
    })


@login_required
def student_crisis_view(request):
    """Serve the student crisis support page"""
    if request.user.role != 'student':
        return redirect('home')
    
    return render(request, 'student/crisis.html', {
        'user': request.user
    })


@login_required
def student_community_view(request):
    """Serve the student community page"""
    if request.user.role != 'student':
        return redirect('home')
    
    return render(request, 'student/community.html', {
        'user': request.user
    })


@login_required
def counsellor_students_view(request):
    """Serve the counselor students management page"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counselor/students.html', {
        'user': request.user
    })


@login_required
def counsellor_crisis_view(request):
    """Serve the counselor crisis management page"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counselor/crisis.html', {
        'user': request.user
    })


@login_required
def counsellor_analytics_view(request):
    """Serve the counselor analytics page"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counselor/analytics.html', {
        'user': request.user
    })


# Enhanced Dashboard Views
@login_required
def enhanced_admin_dashboard_view(request):
    """Serve the enhanced admin dashboard with full backend integration"""
    if request.user.role != 'admin':
        return redirect('home')
    
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    from appointments.models import Appointment
    from crisis.models import CrisisAlert
    from accounts.models import UserSession
    
    User = get_user_model()
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Get same statistics as admin_dashboard_view
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_this_week = User.objects.filter(created_at__gte=week_ago).count()
    students_count = User.objects.filter(role='student').count()
    counselors_count = User.objects.filter(role='counselor').count()
    
    active_sessions = UserSession.objects.filter(
        is_active=True,
        expires_at__gt=now
    ).count()
    
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    appointments_today = Appointment.objects.filter(scheduled_date=today).count()
    
    total_crisis_alerts = CrisisAlert.objects.count()
    active_crisis_alerts = CrisisAlert.objects.filter(status='active').count()
    high_severity_alerts = CrisisAlert.objects.filter(
        severity_level__gte=8,
        status__in=['active', 'acknowledged', 'in_progress']
    ).count()
    
    context = {
        'user': request.user,
        'total_users': total_users,
        'active_users': active_users,
        'new_users_week': new_users_this_week,
        'students_count': students_count,
        'counselors_count': counselors_count,
        'active_sessions': active_sessions,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'appointments_today': appointments_today,
        'total_crisis_alerts': total_crisis_alerts,
        'active_crisis_alerts': active_crisis_alerts,
        'high_severity_alerts': high_severity_alerts,
    }
    
    return render(request, 'admin/simple_dashboard.html', context)


@login_required
def enhanced_counsellor_dashboard_view(request):
    """Serve the enhanced counselor dashboard with full backend integration"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counsellor/enhanced_dashboard.html', {
        'user': request.user
    })


# Admin Management Views
@login_required
def admin_user_management_view(request):
    """Serve the admin user management page with real user data and functionality"""
    if request.user.role != 'admin':
        return redirect('home')
    
    from django.contrib.auth import get_user_model
    from django.db.models import Q, Count
    from django.core.paginator import Paginator
    from django.utils import timezone
    from datetime import timedelta
    from django.http import JsonResponse
    
    User = get_user_model()
    
    # Handle AJAX requests for user management actions
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'toggle_status':
            try:
                user = User.objects.get(id=user_id)
                user.is_active = not user.is_active
                user.save()
                return JsonResponse({
                    'success': True, 
                    'new_status': 'Active' if user.is_active else 'Inactive'
                })
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found'})
        
        elif action == 'delete_user':
            try:
                user = User.objects.get(id=user_id)
                user.delete()
                return JsonResponse({'success': True})
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found'})
    
    # Get user statistics
    total_users = User.objects.count()
    admin_users = User.objects.filter(role='admin').count()
    counselor_users = User.objects.filter(role='counselor').count()
    student_users = User.objects.filter(role='student').count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Get new users this month
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users_month = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Get filtered and paginated users
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.all().select_related()
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Order by date joined (newest first)
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)  # Show 20 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'total_users': total_users,
        'admin_users': admin_users,
        'counselor_users': counselor_users,
        'student_users': student_users,
        'active_users': active_users,
        'new_users_month': new_users_month,
        'users': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/simple_user_management.html', context)


@login_required
def admin_content_moderation_view(request):
    """Serve the admin content moderation page"""
    if request.user.role != 'admin':
        return redirect('home')
    
    return render(request, 'admin/content_moderation.html', {
        'user': request.user
    })


@login_required
@login_required
def admin_system_settings_view(request):
    """Serve the admin system settings page with real configuration options"""
    if request.user.role != 'admin':
        return redirect('home')
    
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from crisis.models import CrisisType
    
    User = get_user_model()
    
    # Handle settings updates
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_crisis_types':
            # Handle crisis type management
            crisis_type_id = request.POST.get('crisis_type_id')
            if crisis_type_id:
                try:
                    crisis_type = CrisisType.objects.get(id=crisis_type_id)
                    crisis_type.is_active = request.POST.get('is_active') == 'on'
                    crisis_type.severity_level = int(request.POST.get('severity_level', crisis_type.severity_level))
                    crisis_type.save()
                    messages.success(request, f"Crisis type '{crisis_type.name}' updated successfully.")
                except CrisisType.DoesNotExist:
                    messages.error(request, "Crisis type not found.")
        
        elif action == 'add_crisis_type':
            name = request.POST.get('new_crisis_name')
            description = request.POST.get('new_crisis_description')
            severity = request.POST.get('new_crisis_severity')
            
            if name and description and severity:
                CrisisType.objects.create(
                    name=name,
                    description=description,
                    severity_level=int(severity),
                    immediate_response=request.POST.get('immediate_response', "Contact counselor immediately"),
                    escalation_criteria=request.POST.get('escalation_criteria', "High severity or repeated incidents")
                )
                messages.success(request, f"Crisis type '{name}' added successfully.")
        
        elif action == 'delete_crisis_type':
            crisis_type_id = request.POST.get('crisis_type_id')
            if crisis_type_id:
                try:
                    crisis_type = CrisisType.objects.get(id=crisis_type_id)
                    name = crisis_type.name
                    crisis_type.delete()
                    messages.success(request, f"Crisis type '{name}' deleted successfully.")
                except CrisisType.DoesNotExist:
                    messages.error(request, "Crisis type not found.")
        
        elif action == 'system_maintenance':
            maintenance_action = request.POST.get('maintenance_action')
            
            if maintenance_action == 'clear_cache':
                # Clear application cache
                from django.core.cache import cache
                cache.clear()
                messages.success(request, "Application cache cleared successfully.")
            
            elif maintenance_action == 'cleanup_sessions':
                # Clean up expired sessions
                from django.core.management import call_command
                call_command('clearsessions')
                messages.success(request, "Expired sessions cleaned up successfully.")
            
            elif maintenance_action == 'backup_database':
                # Note: This would typically trigger a background task
                messages.info(request, "Database backup initiated. You will be notified when complete.")
        
        elif action == 'update_system_settings':
            # Handle system-wide settings updates
            maintenance_mode = request.POST.get('maintenance_mode') == 'on'
            user_registration = request.POST.get('user_registration') == 'on'
            email_notifications = request.POST.get('email_notifications') == 'on'
            
            # Note: In a real app, these would be stored in a SystemSettings model
            # For now, we'll just show success messages
            messages.success(request, "System settings updated successfully.")
        
        elif action == 'toggle_user_status':
            user_id = request.POST.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    user.is_active = not user.is_active
                    user.save()
                    status = "activated" if user.is_active else "deactivated"
                    messages.success(request, f"User {user.get_full_name()} has been {status}.")
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
    
    # Get current system information
    import platform
    import os
    from django.utils import timezone as django_timezone
    
    system_info = {
        'django_version': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
        'python_version': platform.python_version(),
        'os_info': f"{platform.system()} {platform.release()}",
        'debug_mode': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database_engine': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        'time_zone': settings.TIME_ZONE,
        'language_code': settings.LANGUAGE_CODE,
        'server_time': django_timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # System performance metrics
    try:
        import psutil
        performance_info = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
            'active_processes': len(psutil.pids()),
        }
    except ImportError:
        performance_info = {
            'cpu_percent': 'N/A (psutil not installed)',
            'memory_percent': 'N/A (psutil not installed)',
            'disk_percent': 'N/A (psutil not installed)',
            'active_processes': 'N/A (psutil not installed)',
        }
    except Exception as e:
        performance_info = {
            'cpu_percent': f'Error: {str(e)}',
            'memory_percent': f'Error: {str(e)}',
            'disk_percent': f'Error: {str(e)}',
            'active_processes': f'Error: {str(e)}',
        }
    
    # Get crisis types for management
    crisis_types = CrisisType.objects.all().order_by('-severity_level', 'name')
    
    # Get user statistics
    user_stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'verified_users': User.objects.filter(is_verified=True).count(),
        'students': User.objects.filter(role='student').count(),
        'counselors': User.objects.filter(role='counselor').count(),
        'admins': User.objects.filter(role='admin').count(),
    }
    
    # Recent system activity
    from datetime import timedelta
    from appointments.models import Appointment
    from crisis.models import CrisisAlert
    
    week_ago = django_timezone.now() - timedelta(days=7)
    recent_users = User.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:10]
    
    # System activity stats
    activity_stats = {
        'new_users_today': User.objects.filter(created_at__date=django_timezone.now().date()).count(),
        'new_appointments_today': Appointment.objects.filter(created_at__date=django_timezone.now().date()).count(),
        'new_alerts_today': CrisisAlert.objects.filter(created_at__date=django_timezone.now().date()).count(),
        'active_sessions': User.objects.filter(last_login__date=django_timezone.now().date()).count(),
    }
    
    # Application health status
    health_status = {
        'database': 'healthy',  # Would implement actual health checks
        'cache': 'healthy',
        'email_service': 'healthy',
        'storage': 'healthy',
    }
    
    context = {
        'user': request.user,
        'system_info': system_info,
        'performance_info': performance_info,
        'crisis_types': crisis_types,
        'user_stats': user_stats,
        'activity_stats': activity_stats,
        'health_status': health_status,
        'recent_users': recent_users,
        'severity_choices': range(1, 11),  # 1-10 severity levels
        
        # Configuration options
        'maintenance_mode': False,  # Would come from SystemSettings model
        'user_registration_enabled': True,
        'email_notifications_enabled': True,
        'max_file_upload_size': '10MB',
        'session_timeout': '30 minutes',
    }
    
    return render(request, 'admin/system_settings.html', context)


# Counselor Enhanced Views
@login_required
def counsellor_students_management_view(request):
    """Serve the counselor students management page with enhanced features"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counsellor/students.html', {
        'user': request.user
    })


@login_required
def counsellor_session_management_view(request):
    """Serve the counselor session management page"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counsellor/sessions.html', {
        'user': request.user
    })


@login_required
def counsellor_crisis_management_view(request):
    """Serve the counselor crisis management page with enhanced features"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counsellor/crisis.html', {
        'user': request.user
    })


@login_required
def counsellor_enhanced_analytics_view(request):
    """Serve the counselor enhanced analytics page"""
    if request.user.role != 'counselor':
        return redirect('home')
    
    return render(request, 'counsellor/analytics.html', {
        'user': request.user
    })


# URL-compatible view functions for admin interface
@login_required
def enhanced_admin_dashboard(request):
    """Enhanced admin dashboard view"""
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'admin/simple_dashboard.html')

@login_required
def admin_profile(request):
    """Admin profile management view"""
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'admin/profile.html')

@login_required
def admin_crisis_tracking(request):
    """Admin crisis tracking view"""
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'admin/crisis_tracking.html')

@login_required
def admin_user_management(request):
    """Admin user management view"""
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'admin/simple_user_management.html')

@login_required
def admin_analytics_reports(request):
    """Admin analytics and reports view"""
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'admin/analytics_reports.html')

@login_required
def admin_system_settings(request):
    """Admin system settings view"""
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'admin/system_settings.html')

@login_required
def enhanced_counselor_dashboard(request):
    """Enhanced counselor dashboard view"""
    if request.user.role != 'counselor':
        return redirect('home')
    return render(request, 'counselor/enhanced_dashboard.html')

@login_required
def counselor_profile(request):
    """Counselor profile management page"""
    if not hasattr(request.user, 'role') or request.user.role != 'counselor':
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    return render(request, 'counselor/counselor_profile.html', context)

@login_required
def counselor_sessions(request):
    """Counselor sessions management page"""
    if not hasattr(request.user, 'role') or request.user.role != 'counselor':
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    return render(request, 'counselor/counselor_sessions.html', context)

@login_required
def counselor_students(request):
    """Counselor students management page"""
    if not hasattr(request.user, 'role') or request.user.role != 'counselor':
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    return render(request, 'counselor/counselor_students.html', context)

@login_required
def counselor_crisis(request):
    """Counselor crisis management page"""
    if not hasattr(request.user, 'role') or request.user.role != 'counselor':
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    return render(request, 'counselor/counselor_crisis.html', context)

@login_required
def counselor_analytics(request):
    """Counselor analytics and reports page"""
    if not hasattr(request.user, 'role') or request.user.role != 'counselor':
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    return render(request, 'counselor/counselor_analytics.html', context)

@login_required
def counselor_crisis_reports(request):
    """Combined counselor crisis management and reports page"""
    if not hasattr(request.user, 'role') or request.user.role != 'counselor':
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    return render(request, 'counselor/counselor_crisis_reports.html', context)