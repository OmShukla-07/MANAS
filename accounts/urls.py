"""
URL configuration for accounts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# We'll add viewsets here later if needed
router = DefaultRouter()

app_name = 'accounts'

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password management
    path('password/change/', views.ChangePasswordView.as_view(), name='change_password'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Profile management
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/update/', views.UserUpdateView.as_view(), name='profile_update'),
    path('profile/student/', views.StudentProfileView.as_view(), name='student_profile'),
    path('profile/counselor/', views.CounselorProfileView.as_view(), name='counselor_profile'),
    path('profile/admin/', views.AdminProfileView.as_view(), name='admin_profile'),
    
    # Dashboard and utilities
    path('dashboard/', views.user_dashboard_data, name='dashboard'),
    path('verify-email/', views.verify_email, name='verify_email'),
    
    # Public endpoints
    path('counselors/', views.CounselorListView.as_view(), name='counselor_list'),
    path('app-info/', views.app_info, name='app_info'),
    
    # Admin endpoints
    path('admin/users/', views.UserListView.as_view(), name='admin_user_list'),
    path('admin/stats/', views.admin_stats, name='admin_stats'),
    path('admin/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('admin/counselors/<int:counselor_id>/verify/', views.verify_counselor, name='verify_counselor'),
]