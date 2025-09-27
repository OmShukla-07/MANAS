"""
URL configuration for frontend views.
"""

from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, Http404
from django.views.generic import TemplateView
import os
from . import frontend_views

# Function to serve frontend HTML files
def serve_frontend_file(request, file_path):
    """Serve static HTML files from frontend directory"""
    if file_path == '':
        file_path = 'index.html'
    
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', file_path)
    
    if os.path.exists(frontend_path) and os.path.isfile(frontend_path):
        return FileResponse(open(frontend_path, 'rb'))
    else:
        raise Http404("Frontend file not found")

urlpatterns = [
    # Frontend authentication URLs (pure HTML/CSS/JS interface)
    path('', frontend_views.home_view, name='landing'),  # Landing page with AI chatbot info
    path('home/', frontend_views.home_view, name='home'),  # Home alias
    path('learn-more/', TemplateView.as_view(template_name='learn_more.html'), name='learn_more'),  # Learn more page
    path('landing-premium/', frontend_views.home_view, name='landing_premium'),  # Premium landing alias
    path('login/', frontend_views.login_view, name='login'),  # Clean HTML login page
    path('choose-user/', frontend_views.choose_user_view, name='choose_user'),  # New clean user selection
    path('user-selection/', frontend_views.redirect_old_user_selection, name='redirect_old'),  # Redirect old URL
    path('auth/user-selection/', frontend_views.redirect_old_user_selection, name='redirect_old_auth'),  # Redirect old auth URL
    path('signup/', frontend_views.choose_user_view, name='signup'),  # Redirect to user selection page
    
    # Registration flow for specific user types (enhanced with profile data collection)
    path('signup/student/', frontend_views.student_signup_simple_view, name='student_signup'),
    path('signup/counselor/', frontend_views.counselor_signup_simple_view, name='counselor_signup'),
    path('signup/admin/', frontend_views.admin_signup_simple_view, name='admin_signup'),
    
    # Additional signup page aliases (for compatibility)
    path('student-signup/', frontend_views.student_signup_simple_view, name='student_signup_page'),
    path('counselor-signup/', frontend_views.counselor_signup_simple_view, name='counselor_signup_page'),
    path('admin-signup/', frontend_views.admin_signup_simple_view, name='admin_signup_page'),
    
    # Original authentication URLs (kept for backwards compatibility)
    path('login-old/', frontend_views.login_view, name='login_old'),
    path('signup-old/', frontend_views.signup_view, name='signup_old'),
    
    # Authentication utilities
    path('logout/', frontend_views.logout_view, name='logout'),
    path('forgot-password/', frontend_views.forgot_password_view, name='forgot_password'),
    path('privacy/', frontend_views.privacy_view, name='privacy_view'),  # Fixed name
    path('terms/', frontend_views.terms_view, name='terms_view'),
    
    # Profile and Settings URLs
    path('profile/', frontend_views.profile_view, name='profile'),
    path('settings/', frontend_views.settings_view, name='settings'),
    
    # Student URLs
    path('student/', frontend_views.student_dashboard_view, name='student_dashboard'),
    path('student/enhanced/', frontend_views.enhanced_student_dashboard_view, name='enhanced_student_dashboard'),
    path('student/profile/', frontend_views.student_profile_view, name='student_profile'),
    path('student/appointments/', frontend_views.student_appointments_view, name='student_appointments'),
    path('student/assessments/', frontend_views.student_assessments_view, name='student_assessments'),
    path('student/wellness/', frontend_views.student_wellness_view, name='student_wellness'),
    path('student/crisis/', frontend_views.student_crisis_view, name='student_crisis'),
    path('student/community/', frontend_views.student_community_view, name='student_community'),
    path('student/manas-ai/', frontend_views.student_manas_ai_view, name='student_manas_ai'),
    path('student/resources/', frontend_views.student_resources_view, name='student_resources'),
    path('student/game-zone/', frontend_views.student_game_zone_view, name='student_game_zone'),
    path('student/peer-support/', frontend_views.student_peer_support_view, name='student_peer_support'),
    
    # Counsellor URLs (old)
    path('counsellor/', frontend_views.counsellor_dashboard_view, name='counsellor_dashboard'),
    path('counsellor/enhanced/', frontend_views.enhanced_counsellor_dashboard_view, name='enhanced_counsellor_dashboard'),
    path('counsellor/profile/', frontend_views.counsellor_profile_view, name='counsellor_profile'),
    path('counsellor/sessions/', frontend_views.counsellor_sessions_view, name='counsellor_sessions'),
    path('counsellor/session-management/', frontend_views.counsellor_session_management_view, name='counsellor_session_management'),
    path('counsellor/students/', frontend_views.counsellor_students_view, name='counsellor_students'),
    path('counsellor/students-management/', frontend_views.counsellor_students_management_view, name='counsellor_students_management'),
    path('counsellor/crisis/', frontend_views.counsellor_crisis_view, name='counsellor_crisis'),
    path('counsellor/crisis-management/', frontend_views.counsellor_crisis_management_view, name='counsellor_crisis_management'),
    path('counsellor/analytics/', frontend_views.counsellor_analytics_view, name='counsellor_analytics'),
    path('counsellor/enhanced-analytics/', frontend_views.counsellor_enhanced_analytics_view, name='counsellor_enhanced_analytics'),
    
    # New Counselor Panel URLs (with purple theme)
    path('counselor-panel/', frontend_views.counsellor_dashboard_view, name='counselor_dashboard'),
    path('counselor-panel/profile/', frontend_views.counselor_profile, name='counselor_profile'),
    path('counselor-panel/sessions/', frontend_views.counselor_sessions, name='counselor_sessions'),
    path('counselor-panel/students/', frontend_views.counselor_students, name='counselor_students'),
    path('counselor-panel/crisis/', frontend_views.counselor_crisis, name='counselor_crisis'),
    path('counselor-panel/crisis-reports/', frontend_views.counselor_crisis_reports, name='counselor_crisis_reports'),
    path('counselor-panel/analytics/', frontend_views.counselor_analytics, name='counselor_analytics'),
    
    # Admin URLs
    path('admin-panel/', frontend_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/profile/', frontend_views.admin_profile_view, name='admin_profile'),
    path('admin-panel/crisis-tracking/', frontend_views.admin_crisis_tracking_view, name='admin_crisis_tracking'),
    path('admin-panel/user-management/', frontend_views.admin_user_management_view, name='admin_user_management'),
    path('admin-panel/system-settings/', frontend_views.admin_system_settings_view, name='admin_system_settings'),
    path('admin-panel/content/', frontend_views.admin_content_moderation_view, name='admin_content_moderation'),
    path('admin-panel/css-test/', TemplateView.as_view(template_name='admin/css_test.html'), name='css_test'),
    path('admin-panel/inline-test/', TemplateView.as_view(template_name='admin/inline_test.html'), name='inline_test'),
    path('admin-panel/debug-static/', TemplateView.as_view(template_name='admin/debug_static.html'), name='debug_static'),
    
    # Appointment-related URLs for frontend
    path('appointments/book/', frontend_views.book_appointment_view, name='book_appointment'),
    path('appointments/detail/<uuid:appointment_id>/', frontend_views.appointment_detail_view, name='appointment_detail'),
    path('appointments/api/available-slots/', frontend_views.get_available_slots, name='get_available_slots'),
    path('appointments/api/cancel/<uuid:appointment_id>/', frontend_views.cancel_appointment, name='cancel_appointment'),
    path('appointments/api/reschedule/<uuid:appointment_id>/', frontend_views.reschedule_appointment, name='reschedule_appointment'),
    path('appointments/api/dashboard-stats/', frontend_views.appointment_dashboard_stats, name='appointment_dashboard_stats'),
    
    # Admin access guide
    path('admin-access/', TemplateView.as_view(template_name='admin_access_guide.html'), name='admin_access_guide'),
    
    # Frontend file serving for standalone HTML files
    path('frontend/<path:file_path>', serve_frontend_file, name='serve_frontend'),
    path('js/manas-api-client.js', serve_frontend_file, {'file_path': 'js/manas-api-client.js'}, name='manas_api_client'),
    path('main-index.html', serve_frontend_file, {'file_path': 'main-index.html'}, name='main_index'),
    path('dashboard.html', serve_frontend_file, {'file_path': 'dashboard.html'}, name='dashboard_html'),
    path('login.html', serve_frontend_file, {'file_path': 'login.html'}, name='login_html'),
    path('signup.html', serve_frontend_file, {'file_path': 'signup.html'}, name='signup_html'),
    path('admin-main.html', serve_frontend_file, {'file_path': 'admin-main.html'}, name='admin_main_html'),
    path('counsellor-dashboard.html', serve_frontend_file, {'file_path': 'counsellor-dashboard.html'}, name='counsellor_dashboard_html'),
    path('student/enhanced_dashboard.html', serve_frontend_file, {'file_path': 'student/enhanced_dashboard.html'}, name='enhanced_student_dashboard_html'),
    path('counselor/enhanced_dashboard.html', serve_frontend_file, {'file_path': 'counselor/enhanced_dashboard.html'}, name='enhanced_counselor_dashboard_html'),
    
    # Admin URLs fixed page
    path('admin-fixed/', TemplateView.as_view(template_name='admin_urls_fixed.html'), name='admin_fixed_guide'),
]