# counselor_urls.py
"""
URL patterns for counselor panel functionality - Complete backend integration
"""

from django.urls import path
from . import counselor_views

# Counselor Panel URLs
counselor_urlpatterns = [
    # Main counselor dashboard
    path('counselor/', counselor_views.counselor_dashboard, name='counselor_dashboard'),
    
    # Session management
    path('sessions/', counselor_views.counselor_sessions, name='counselor_sessions'),
    path('sessions/requests/', counselor_views.counselor_session_requests, name='counselor_session_requests'),
    
    # Connection API
    path('api/connect-session/', counselor_views.connect_session, name='connect_session'),
    
    # Session Room
    path('session-room/<int:appointment_id>/', counselor_views.session_room, name='session_room'),
    
    # Student management
    path('counselor/students/', counselor_views.counselor_students, name='counselor_students'),
    
    # Crisis management
    path('counselor/crisis/', counselor_views.counselor_crisis, name='counselor_crisis'),
    
    # Combined Crisis & Reports page
    path('counselor/crisis-reports/', counselor_views.counselor_crisis_reports, name='counselor_crisis_reports'),
    
    # Analytics
    path('counselor/analytics/', counselor_views.counselor_analytics, name='counselor_analytics'),
    
    # Profile management
    path('counselor/profile/', counselor_views.counselor_profile, name='counselor_profile'),
    
    # Authentication
    path('logout/', counselor_views.counselor_logout, name='logout'),
    
    # Counselor request management APIs
    path('api/counselor/requests/', counselor_views.get_counselor_requests, name='get_counselor_requests'),
    path('api/counselor/requests/handle/', counselor_views.handle_counselor_request, name='handle_counselor_request'),
    path('api/counselor/available/', counselor_views.get_available_counselors, name='get_available_counselors'),
    
    # Calling functionality APIs
    path('api/counselor/call/initiate/', counselor_views.initiate_call, name='initiate_call'),
    path('api/counselor/call/end/', counselor_views.end_call, name='end_call'),
    
    # API endpoints for real functionality
    # Availability management
    path('api/counselor/availability/', counselor_views.update_availability, name='update_availability'),
    
    # Crisis management APIs
    path('api/counselor/crisis/create/', counselor_views.create_crisis_alert, name='create_crisis_alert'),
    path('api/counselor/crisis/<int:alert_id>/resolve/', counselor_views.resolve_crisis_alert, name='resolve_crisis_alert'),
    path('api/counselor/crisis/action/', counselor_views.handle_crisis_action, name='handle_crisis_action'),
    
    # Session management APIs
    path('api/counselor/sessions/schedule/', counselor_views.schedule_session, name='schedule_session'),
    path('api/counselor/sessions/<int:appointment_id>/update/', counselor_views.update_session_status, name='update_session_status'),
    path('api/counselor/calendar/events/', counselor_views.calendar_events_api, name='calendar_events_api'),
    
    # Student management APIs
    path('api/counselor/students/<int:student_id>/details/', counselor_views.student_details_api, name='student_details_api'),
    
    # Profile management APIs
    path('api/counselor/profile/update/', counselor_views.update_counselor_profile, name='update_counselor_profile'),
    path('api/counselor/profile/password/', counselor_views.change_password_api, name='change_password_api'),
    
    # Analytics and data export APIs
    path('api/counselor/analytics/sessions/', counselor_views.session_analytics_data, name='session_analytics_data'),
    path('api/counselor/export/<str:export_type>/', counselor_views.export_data, name='export_data'),
]