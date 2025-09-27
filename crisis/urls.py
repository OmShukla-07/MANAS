"""
URLs for the crisis app.
Handles crisis detection, alerts, emergency response, and safety planning.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'crisis'

router = DefaultRouter()

urlpatterns = [
    # Crisis Types
    path('types/', views.CrisisTypeListView.as_view(), name='crisis-types'),
    
    # Crisis Alerts
    path('alerts/', views.CrisisAlertListView.as_view(), name='alert-list'),
    path('alerts/<int:pk>/', views.CrisisAlertDetailView.as_view(), name='alert-detail'),
    path('alerts/<int:alert_id>/assign/', views.AssignCrisisAlertView.as_view(), name='alert-assign'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_crisis_alert, name='alert-resolve'),
    path('alerts/create/', views.create_crisis_alert, name='alert-create'),
    
    # Crisis Responses
    path('responses/', views.CrisisResponseListCreateView.as_view(), name='response-list'),
    
    # Safety Plans
    path('safety-plans/', views.SafetyPlanListCreateView.as_view(), name='safety-plan-list'),
    path('safety-plans/<int:pk>/', views.SafetyPlanDetailView.as_view(), name='safety-plan-detail'),
    path('safety-plans/<int:plan_id>/activate/', views.activate_safety_plan, name='safety-plan-activate'),
    
    # Crisis Resources
    path('resources/', views.CrisisResourceListView.as_view(), name='resource-list'),
    path('resources/<int:pk>/', views.CrisisResourceDetailView.as_view(), name='resource-detail'),
    path('resources/emergency/', views.emergency_resources, name='emergency-resources'),
    
    # Follow-ups
    path('follow-ups/', views.CrisisFollowUpListCreateView.as_view(), name='follow-up-list'),
    
    # Dashboard
    path('dashboard/', views.CrisisDashboardView.as_view(), name='crisis-dashboard'),
    
    # Router URLs
    path('', include(router.urls)),
]