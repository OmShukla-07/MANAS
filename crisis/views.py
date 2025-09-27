"""
API views for the crisis app.
Handles crisis detection, alerts, emergency response, and safety planning.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q, Max
from django.utils import timezone
from datetime import timedelta, datetime
import statistics

from .models import (
    CrisisType, CrisisAlert, CrisisResponse, SafetyPlan, 
    CrisisResource, CrisisFollowUp, CrisisAnalytics
)
from .serializers import (
    CrisisTypeSerializer, CrisisAlertListSerializer, CrisisAlertDetailSerializer,
    CrisisAlertCreateSerializer, CrisisResponseSerializer, CrisisResponseCreateSerializer,
    SafetyPlanSerializer, SafetyPlanCreateUpdateSerializer, CrisisResourceSerializer,
    CrisisResourceListSerializer, CrisisFollowUpSerializer, CrisisFollowUpCreateSerializer,
    CrisisAnalyticsSerializer, CrisisDashboardSerializer, CrisisStatsSerializer,
    UserCrisisStatusSerializer, EmergencyContactSerializer, QuickResponseActionSerializer,
    CrisisInterventionSerializer
)

User = get_user_model()


# Crisis Types (Admin/Counselor only)
class CrisisTypeListView(generics.ListAPIView):
    """List all crisis types"""
    queryset = CrisisType.objects.filter(is_active=True).order_by('-severity_level')
    serializer_class = CrisisTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role in ['counselor', 'admin']:
            return super().get_queryset()
        # Students see limited info
        return CrisisType.objects.filter(is_active=True).values('id', 'name', 'description')


# Crisis Alerts Management
class CrisisAlertListView(generics.ListCreateAPIView):
    """List crisis alerts and create new ones"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CrisisAlertCreateSerializer
        return CrisisAlertListSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = CrisisAlert.objects.select_related(
            'user', 'crisis_type', 'assigned_counselor'
        )
        
        if user.role == 'student':
            # Students only see their own alerts
            queryset = queryset.filter(user=user)
        elif user.role == 'counselor':
            # Counselors see alerts assigned to them or unassigned high-priority ones
            queryset = queryset.filter(
                Q(assigned_counselor=user) | 
                Q(assigned_counselor__isnull=True, severity_level__gte=7)
            )
        # Admins see all alerts (no additional filtering)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by severity
        min_severity = self.request.query_params.get('min_severity')
        if min_severity:
            try:
                queryset = queryset.filter(severity_level__gte=int(min_severity))
            except ValueError:
                pass
        
        # Filter by date range
        days = self.request.query_params.get('days', 7)
        try:
            days = int(days)
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created_at__gte=start_date)
        except ValueError:
            pass
        
        return queryset.order_by('-severity_level', '-created_at')


class CrisisAlertDetailView(generics.RetrieveUpdateAPIView):
    """Detailed view of a crisis alert"""
    serializer_class = CrisisAlertDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = CrisisAlert.objects.select_related('user', 'crisis_type', 'assigned_counselor')
        
        if user.role == 'student':
            return queryset.filter(user=user)
        elif user.role == 'counselor':
            return queryset.filter(
                Q(assigned_counselor=user) | Q(assigned_counselor__isnull=True)
            )
        return queryset  # Admin sees all


class AssignCrisisAlertView(APIView):
    """Assign crisis alert to counselor"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, alert_id):
        if request.user.role not in ['counselor', 'admin']:
            return Response(
                {"error": "Only counselors and admins can assign alerts"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            alert = CrisisAlert.objects.get(id=alert_id)
            counselor_id = request.data.get('counselor_id')
            
            if counselor_id:
                counselor = User.objects.get(id=counselor_id, role='counselor')
                alert.assigned_counselor = counselor
            else:
                alert.assigned_counselor = request.user
            
            alert.status = 'acknowledged'
            alert.acknowledged_at = timezone.now()
            alert.save()
            
            return Response(CrisisAlertDetailSerializer(alert).data)
            
        except CrisisAlert.DoesNotExist:
            return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "Counselor not found"}, status=status.HTTP_404_NOT_FOUND)


# Crisis Response Management
class CrisisResponseListCreateView(generics.ListCreateAPIView):
    """List and create crisis responses"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CrisisResponseCreateSerializer
        return CrisisResponseSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = CrisisResponse.objects.select_related('alert', 'responder')
        
        if user.role == 'student':
            queryset = queryset.filter(alert__user=user)
        elif user.role == 'counselor':
            queryset = queryset.filter(
                Q(responder=user) | Q(alert__assigned_counselor=user)
            )
        
        alert_id = self.request.query_params.get('alert')
        if alert_id:
            queryset = queryset.filter(alert_id=alert_id)
        
        return queryset.order_by('-created_at')


# Safety Plans Management
class SafetyPlanListCreateView(generics.ListCreateAPIView):
    """List and create safety plans"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SafetyPlanCreateUpdateSerializer
        return SafetyPlanSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = SafetyPlan.objects.select_related('user', 'created_by')
        
        if user.role == 'student':
            queryset = queryset.filter(user=user)
        elif user.role == 'counselor':
            # Counselors see plans they created or for their assigned students
            queryset = queryset.filter(
                Q(created_by=user) | Q(user__in=self._get_assigned_students(user))
            )
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-updated_at')
    
    def _get_assigned_students(self, counselor):
        """Get students assigned to this counselor"""
        # This would be based on your appointment/assignment logic
        from appointments.models import Appointment
        return User.objects.filter(
            role='student',
            appointments_as_student__counselor=counselor
        ).distinct()


class SafetyPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detailed view of safety plan"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SafetyPlanCreateUpdateSerializer
        return SafetyPlanSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = SafetyPlan.objects.select_related('user', 'created_by')
        
        if user.role == 'student':
            return queryset.filter(user=user)
        elif user.role == 'counselor':
            return queryset.filter(
                Q(created_by=user) | Q(user__in=self._get_assigned_students(user))
            )
        return queryset
    
    def _get_assigned_students(self, counselor):
        from appointments.models import Appointment
        return User.objects.filter(
            role='student',
            appointments_as_student__counselor=counselor
        ).distinct()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def activate_safety_plan(request, plan_id):
    """Activate a safety plan during crisis"""
    try:
        if request.user.role == 'student':
            plan = SafetyPlan.objects.get(id=plan_id, user=request.user)
        else:
            plan = SafetyPlan.objects.get(id=plan_id)
        
        plan.times_activated += 1
        plan.save()
        
        # Create crisis alert if none exists
        if not CrisisAlert.objects.filter(
            user=plan.user, 
            status__in=['active', 'acknowledged'],
            created_at__gte=timezone.now() - timedelta(hours=2)
        ).exists():
            
            crisis_type = CrisisType.objects.filter(
                name__icontains='safety plan'
            ).first() or CrisisType.objects.first()
            
            CrisisAlert.objects.create(
                user=plan.user,
                crisis_type=crisis_type,
                source='safety_plan_activation',
                severity_level=8,
                confidence_score=1.0,
                description=f"Safety plan '{plan.title}' has been activated",
                context_data={'safety_plan_id': str(plan.id)}
            )
        
        return Response({
            'message': 'Safety plan activated successfully',
            'plan': SafetyPlanSerializer(plan).data
        })
        
    except SafetyPlan.DoesNotExist:
        return Response({"error": "Safety plan not found"}, status=status.HTTP_404_NOT_FOUND)


# Crisis Resources
class CrisisResourceListView(generics.ListAPIView):
    """List crisis resources"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.query_params.get('detailed'):
            return CrisisResourceSerializer
        return CrisisResourceListSerializer
    
    def get_queryset(self):
        queryset = CrisisResource.objects.filter(is_active=True)
        
        resource_type = self.request.query_params.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(
                Q(location__icontains=location) | 
                Q(serves_areas__contains=[location])
            )
        
        if self.request.query_params.get('emergency_only'):
            queryset = queryset.filter(availability='24/7')
        
        if self.request.query_params.get('free_only'):
            queryset = queryset.filter(is_free=True)
        
        return queryset.order_by('-is_featured', 'display_order', 'name')


class CrisisResourceDetailView(generics.RetrieveAPIView):
    """Detailed view of crisis resource"""
    queryset = CrisisResource.objects.filter(is_active=True)
    serializer_class = CrisisResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Track resource access
        instance.click_count += 1
        instance.save(update_fields=['click_count'])
        return super().retrieve(request, *args, **kwargs)


# Follow-ups Management
class CrisisFollowUpListCreateView(generics.ListCreateAPIView):
    """List and create crisis follow-ups"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CrisisFollowUpCreateSerializer
        return CrisisFollowUpSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = CrisisFollowUp.objects.select_related('alert', 'assigned_to')
        
        if user.role == 'student':
            queryset = queryset.filter(alert__user=user)
        elif user.role == 'counselor':
            queryset = queryset.filter(assigned_to=user)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if self.request.query_params.get('overdue'):
            queryset = queryset.filter(
                scheduled_date__lt=timezone.now(),
                status='scheduled'
            )
        
        return queryset.order_by('scheduled_date')


# Dashboard and Analytics
class CrisisDashboardView(APIView):
    """Crisis management dashboard"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.role not in ['counselor', 'admin']:
            return Response(
                {"error": "Access denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Active alerts
        active_alerts = CrisisAlert.objects.filter(status='active')
        if user.role == 'counselor':
            active_alerts = active_alerts.filter(
                Q(assigned_counselor=user) | Q(assigned_counselor__isnull=True)
            )
        
        # High priority alerts (severity >= 7)
        high_priority = active_alerts.filter(severity_level__gte=7)
        
        # Recent alerts (last 24 hours)
        recent_alerts = CrisisAlert.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        )
        if user.role == 'counselor':
            recent_alerts = recent_alerts.filter(assigned_counselor=user)
        
        # Pending follow-ups
        pending_follow_ups = CrisisFollowUp.objects.filter(
            status='scheduled',
            scheduled_date__lte=timezone.now() + timedelta(days=1)
        )
        if user.role == 'counselor':
            pending_follow_ups = pending_follow_ups.filter(assigned_to=user)
        
        # Stats
        stats = self._calculate_crisis_stats(user)
        
        dashboard_data = {
            'active_alerts': CrisisAlertListSerializer(active_alerts[:10], many=True).data,
            'high_priority_alerts': CrisisAlertListSerializer(high_priority[:5], many=True).data,
            'recent_alerts': CrisisAlertListSerializer(recent_alerts[:10], many=True).data,
            'pending_follow_ups': CrisisFollowUpSerializer(pending_follow_ups[:10], many=True).data,
            'stats': stats
        }
        
        return Response(dashboard_data)
    
    def _calculate_crisis_stats(self, user):
        """Calculate crisis statistics"""
        today = timezone.now().date()
        
        base_query = CrisisAlert.objects
        if user.role == 'counselor':
            base_query = base_query.filter(assigned_counselor=user)
        
        stats = {
            'total_alerts_today': base_query.filter(created_at__date=today).count(),
            'active_alerts': base_query.filter(status='active').count(),
            'high_severity_alerts': base_query.filter(
                status='active', 
                severity_level__gte=7
            ).count(),
            'average_response_time_minutes': 0,
            'alerts_by_type': {},
            'alerts_by_hour': [0] * 24,
            'resolution_rate': 0
        }
        
        # Calculate average response time
        responses = CrisisResponse.objects.filter(
            alert__created_at__date=today
        )
        if user.role == 'counselor':
            responses = responses.filter(responder=user)
        
        if responses.exists():
            avg_response = responses.aggregate(
                avg_time=Avg('response_time')
            )['avg_time']
            if avg_response:
                stats['average_response_time_minutes'] = avg_response.total_seconds() / 60
        
        # Alerts by type
        type_counts = base_query.filter(
            created_at__gte=today
        ).values('crisis_type__name').annotate(count=Count('id'))
        
        stats['alerts_by_type'] = {
            item['crisis_type__name']: item['count'] 
            for item in type_counts
        }
        
        # Resolution rate
        total_week = base_query.filter(
            created_at__gte=today - timedelta(days=7)
        ).count()
        resolved_week = base_query.filter(
            created_at__gte=today - timedelta(days=7),
            status='resolved'
        ).count()
        
        if total_week > 0:
            stats['resolution_rate'] = (resolved_week / total_week) * 100
        
        return stats


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_crisis_alert(request):
    """Create a crisis alert from various sources"""
    serializer = CrisisAlertCreateSerializer(data=request.data)
    if serializer.is_valid():
        alert = serializer.save()
        
        # Trigger immediate response for high severity
        if alert.severity_level >= 8:
            # Auto-assign to available counselor
            available_counselor = User.objects.filter(
                role='counselor',
                is_active=True
            ).exclude(
                assigned_crisis_alerts__status='active'
            ).first()
            
            if available_counselor:
                alert.assigned_counselor = available_counselor
                alert.save()
        
        return Response(
            CrisisAlertDetailSerializer(alert).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def emergency_resources(request):
    """Get immediate emergency resources"""
    
    # Get location from request
    location = request.query_params.get('location', '')
    
    # Emergency hotlines (24/7)
    hotlines = CrisisResource.objects.filter(
        resource_type='hotline',
        availability='24/7',
        is_active=True
    ).order_by('-is_featured', 'display_order')[:3]
    
    # Local emergency services
    emergency_services = CrisisResource.objects.filter(
        resource_type='emergency_service',
        is_active=True
    )
    
    if location:
        emergency_services = emergency_services.filter(
            Q(location__icontains=location) | Q(serves_areas__contains=[location])
        )
    
    # Chat services
    chat_services = CrisisResource.objects.filter(
        resource_type='online_chat',
        is_active=True
    ).order_by('-is_featured')[:2]
    
    # Text services
    text_services = CrisisResource.objects.filter(
        resource_type='text_service',
        is_active=True
    ).order_by('-is_featured')[:2]
    
    resources = {
        'hotlines': CrisisResourceListSerializer(hotlines, many=True).data,
        'emergency_services': CrisisResourceListSerializer(emergency_services[:3], many=True).data,
        'chat_services': CrisisResourceListSerializer(chat_services, many=True).data,
        'text_services': CrisisResourceListSerializer(text_services, many=True).data,
    }
    
    return Response(resources)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resolve_crisis_alert(request, alert_id):
    """Mark a crisis alert as resolved"""
    
    if request.user.role not in ['counselor', 'admin']:
        return Response(
            {"error": "Only counselors and admins can resolve alerts"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        alert = CrisisAlert.objects.get(id=alert_id)
        
        if request.user.role == 'counselor' and alert.assigned_counselor != request.user:
            return Response(
                {"error": "You can only resolve alerts assigned to you"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.resolution_time = alert.resolved_at - alert.created_at
        alert.save()
        
        # Create follow-up if required
        if alert.follow_up_required:
            follow_up_date = timezone.now() + timedelta(days=1)
            CrisisFollowUp.objects.create(
                alert=alert,
                assigned_to=alert.assigned_counselor or request.user,
                follow_up_type='check_in',
                scheduled_date=follow_up_date,
                purpose='Post-crisis wellness check-in'
            )
        
        return Response(CrisisAlertDetailSerializer(alert).data)
        
    except CrisisAlert.DoesNotExist:
        return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
