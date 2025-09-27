"""
URLs for the core app.
Handles system management, notifications, FAQs, and analytics.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView

from . import views
from . import counselor_views
from .counselor_urls import counselor_urlpatterns

app_name = 'core'

router = DefaultRouter()

urlpatterns = [
    # Counselor Panel URLs (add at the beginning for priority)
    *counselor_urlpatterns,
    
    # Session room accessible by both students and counselors
    path('session/<int:appointment_id>/', counselor_views.session_room, name='session_room_public'),
    
    # Demo workflow page
    path('demo/', TemplateView.as_view(template_name='demo_workflow.html'), name='demo_workflow'),
    
    # System Configuration
    path('config/', views.SystemConfigurationListView.as_view(), name='config-list'),
    path('config/public/', views.PublicSystemConfigurationView.as_view(), name='config-public'),
    path('config/<int:pk>/', views.SystemConfigurationDetailView.as_view(), name='config-detail'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/create/', views.NotificationCreateView.as_view(), name='notification-create'),
    path('notifications/mark-read/', views.mark_notifications_read, name='notifications-mark-read'),
    path('notifications/delete/', views.delete_notifications, name='notifications-delete'),
    path('notifications/stats/', views.notification_stats, name='notification-stats'),
    
    # FAQs
    path('faqs/', views.FAQListView.as_view(), name='faq-list'),
    path('faqs/<int:pk>/', views.FAQDetailView.as_view(), name='faq-detail'),
    path('faqs/<int:faq_id>/rate/', views.rate_faq_helpfulness, name='faq-rate'),
    
    # FAQ Management
    path('admin/faqs/', views.FAQManagementListCreateView.as_view(), name='faq-management-list'),
    path('admin/faqs/<int:pk>/', views.FAQManagementDetailView.as_view(), name='faq-management-detail'),
    
    # Contact Messages
    path('contact/', views.ContactMessageCreateView.as_view(), name='contact-create'),
    path('admin/contact-messages/', views.ContactMessageListView.as_view(), name='contact-message-list'),
    path('admin/contact-messages/<int:pk>/', views.ContactMessageDetailView.as_view(), name='contact-message-detail'),
    
    # System Alerts
    path('alerts/', views.SystemAlertListView.as_view(), name='alert-list'),
    path('admin/alerts/', views.SystemAlertManagementView.as_view(), name='alert-management'),
    
    # User Preferences
    path('preferences/', views.UserPreferenceView.as_view(), name='user-preferences'),
    
    # Analytics
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    
    # Dashboard and Stats
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('admin/stats/', views.system_stats, name='system-stats'),
    
    # Enhanced Admin Dashboard API Endpoints
    path('admin/dashboard-stats/', views.admin_dashboard_stats, name='admin-dashboard-stats'),
    path('admin/recent-activity/', views.admin_recent_activity, name='admin-recent-activity'),
    path('admin/system-health/', views.admin_system_health, name='admin-system-health'),
    
    # User Management AJAX
    path('admin/user-action/', views.admin_user_action_ajax, name='admin-user-action-ajax'),
    
    # Supabase Integration
    path('supabase/status/', views.supabase_status, name='supabase-status'),
    path('supabase/migrate/', views.migrate_to_supabase, name='supabase-migrate'),
    path('supabase/setup-guide/', views.supabase_setup_guide, name='supabase-setup-guide'),
    path('supabase/dashboard/', views.supabase_dashboard_view, name='supabase-dashboard'),
    
    # Router URLs
    path('', include(router.urls)),
]