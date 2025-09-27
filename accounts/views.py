from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404

from .models import StudentProfile, CounselorProfile, AdminProfile
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserProfileSerializer,
    UserUpdateSerializer,
    StudentProfileSerializer,
    CounselorProfileSerializer,
    AdminProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    CounselorPublicSerializer,
    UserStatsSerializer,
    UserListSerializer
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User registered successfully',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with user details"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get user from email
            email = request.data.get('email')
            try:
                user = User.objects.get(email=email)
                response.data['user'] = UserProfileSerializer(user).data
            except User.DoesNotExist:
                pass
        
        return response


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserUpdateView(generics.UpdateAPIView):
    """Update basic user information"""
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class StudentProfileView(generics.RetrieveUpdateAPIView):
    """Student profile management"""
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if not self.request.user.is_student:
            raise permissions.PermissionDenied("Only students can access this endpoint.")
        
        profile, created = StudentProfile.objects.get_or_create(user=self.request.user)
        return profile


class CounselorProfileView(generics.RetrieveUpdateAPIView):
    """Counselor profile management"""
    serializer_class = CounselorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if not self.request.user.is_counselor:
            raise permissions.PermissionDenied("Only counselors can access this endpoint.")
        
        profile, created = CounselorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'license_number': f"TEMP_{self.request.user.id}_{self.request.user.email.split('@')[0]}"}
        )
        return profile


class AdminProfileView(generics.RetrieveUpdateAPIView):
    """Admin profile management"""
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if not self.request.user.is_admin:
            raise permissions.PermissionDenied("Only admins can access this endpoint.")
        
        profile, created = AdminProfile.objects.get_or_create(user=self.request.user)
        return profile


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """Request password reset"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            
            # Send email (in production, use proper email template)
            subject = 'MANAS - Password Reset Request'
            message = f'''
            Hi {user.get_full_name()},
            
            You requested a password reset for your MANAS account.
            Click the link below to reset your password:
            
            {reset_link}
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            MANAS Team
            '''
            
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                return Response({'message': 'Password reset email sent successfully'})
            except Exception as e:
                return Response(
                    {'error': 'Failed to send email. Please try again later.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Confirm password reset"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            # Get UID from request (should be passed from frontend)
            uid = request.data.get('uid')
            
            if not uid:
                return Response({'error': 'UID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
                
                if default_token_generator.check_token(user, token):
                    user.set_password(new_password)
                    user.save()
                    return Response({'message': 'Password reset successful'})
                else:
                    return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
                    
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout user by blacklisting refresh token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'})
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


# Public views for listings
class CounselorListView(generics.ListAPIView):
    """Public list of available counselors"""
    serializer_class = CounselorPublicSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return CounselorProfile.objects.filter(
            is_available=True, 
            is_verified=True,
            user__is_active=True
        ).select_related('user')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard_data(request):
    """Get dashboard data based on user role"""
    user = request.user
    
    data = {
        'user': UserProfileSerializer(user).data,
        'role_specific': {}
    }
    
    if user.is_student:
        # Add student-specific dashboard data
        data['role_specific'] = {
            'recent_sessions': [],  # Will be implemented when chat app is ready
            'upcoming_appointments': [],  # Will be implemented when appointments app is ready
            'wellness_streak': 0,  # Will be implemented when wellness app is ready
        }
    elif user.is_counselor:
        # Add counselor-specific dashboard data  
        profile = CounselorProfile.objects.get(user=user)
        data['role_specific'] = {
            'today_appointments': [],  # Will be implemented when appointments app is ready
            'pending_sessions': [],  # Will be implemented when chat app is ready
            'rating': float(profile.average_rating),
        }
    elif user.is_admin:
        # Add admin-specific dashboard data
        data['role_specific'] = {
            'total_users': User.objects.count(),
            'active_sessions': 0,  # Will be implemented when sessions are tracked
            'crisis_alerts': 0,  # Will be implemented when crisis app is ready
        }
    
    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_email(request):
    """Verify user email (placeholder for email verification logic)"""
    # This would typically involve sending a verification email
    # For now, we'll just mark the user as verified
    user = request.user
    user.is_verified = True
    user.save()
    
    return Response({'message': 'Email verified successfully'})


# Admin-only views
class UserListView(generics.ListAPIView):
    """Admin view to list all users"""
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_admin:
            raise permissions.PermissionDenied("Admin access required")
        return User.objects.all().order_by('-date_joined')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_stats(request):
    """Get admin dashboard statistics"""
    if not request.user.is_admin:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role='student').count(),
        'total_counselors': User.objects.filter(role='counselor').count(),
        'total_admins': User.objects.filter(role='admin').count(),
        'active_users_today': User.objects.filter(last_login__date=today).count(),
        'new_registrations_this_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
        'verified_counselors': CounselorProfile.objects.filter(is_verified=True).count(),
        'pending_verifications': CounselorProfile.objects.filter(is_verified=False).count(),
    }
    
    serializer = UserStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_user_status(request, user_id):
    """Admin endpoint to activate/deactivate users"""
    if not request.user.is_admin:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        return Response({
            'message': f"User {'activated' if user.is_active else 'deactivated'} successfully",
            'user': UserListSerializer(user).data
        })
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_counselor(request, counselor_id):
    """Admin endpoint to verify counselor profiles"""
    if not request.user.is_admin:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        counselor = CounselorProfile.objects.get(id=counselor_id)
        counselor.is_verified = True
        counselor.save()
        
        return Response({
            'message': 'Counselor verified successfully',
            'counselor': CounselorProfileSerializer(counselor).data
        })
    except CounselorProfile.DoesNotExist:
        return Response({'error': 'Counselor not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def app_info(request):
    """Get basic app information for frontend"""
    return Response({
        'app_name': 'MANAS',
        'version': '1.0.0',
        'description': 'Mental Health and Nutrition Analysis System',
        'features': [
            'AI-powered mental health chat',
            'Professional counselor appointments',
            'Wellness tracking and goals',
            'Crisis detection and support',
            'Community support groups',
            'Mental health resources'
        ],
        'contact': {
            'support_email': 'support@manas.com',
            'crisis_helpline': '1800-XXX-XXXX'
        }
    })
