"""
URL configuration for appointments app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    # Main appointment views
    path('', views.appointments_list, name='appointments_list'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('detail/<uuid:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    
    # AJAX endpoints
    path('api/available-slots/', views.get_available_slots, name='get_available_slots'),
    path('api/cancel/<uuid:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('api/reschedule/<uuid:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('api/counselor-schedule/<int:counselor_id>/', views.counselor_schedule, name='counselor_schedule'),
    path('api/dashboard-stats/', views.appointment_dashboard_stats, name='appointment_dashboard_stats'),
    
    # REST API
    path('api/', include(router.urls)),
]