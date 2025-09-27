from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser, StudentProfile, CounselorProfile, AdminProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'role', 'password', 'password_confirm', 'phone_number', 'date_of_birth')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = CustomUser.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password.')


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for student profile"""
    
    class Meta:
        model = StudentProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class CounselorProfileSerializer(serializers.ModelSerializer):
    """Serializer for counselor profile"""
    
    class Meta:
        model = CounselorProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'average_rating', 'total_reviews')


class AdminProfileSerializer(serializers.ModelSerializer):
    """Serializer for admin profile"""
    
    class Meta:
        model = AdminProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'last_login', 'login_count')


class UserProfileSerializer(serializers.ModelSerializer):
    """Complete user profile serializer with role-specific data"""
    student_profile = StudentProfileSerializer(read_only=True)
    counselor_profile = CounselorProfileSerializer(read_only=True)
    admin_profile = AdminProfileSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 
                 'phone_number', 'date_of_birth', 'is_verified', 'profile_completed',
                 'created_at', 'updated_at', 'student_profile', 'counselor_profile', 'admin_profile')
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_verified')


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user basic information"""
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'phone_number', 'date_of_birth')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs


# Simplified serializers for API responses
class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for public display"""
    full_name = serializers.ReadOnlyField(source='get_full_name')
    
    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'full_name', 'role')


class CounselorPublicSerializer(serializers.ModelSerializer):
    """Public counselor information for listings"""
    user = UserBasicSerializer(read_only=True)
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = CounselorProfile
        fields = ('user', 'specializations', 'experience_years', 'age', 'gender',
                 'bio', 'languages_spoken', 'consultation_fee', 'availability_status',
                 'session_duration_minutes', 'rating_average', 'total_sessions',
                 'is_verified', 'is_available_for_crisis')
        read_only_fields = ('rating_average', 'total_sessions')


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics (admin dashboard)"""
    total_users = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_counselors = serializers.IntegerField()
    total_admins = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    new_registrations_this_week = serializers.IntegerField()
    verified_counselors = serializers.IntegerField()
    pending_verifications = serializers.IntegerField()


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list views (admin)"""
    full_name = serializers.ReadOnlyField(source='get_full_name')
    profile_completion = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'full_name', 'role',
            'is_active', 'date_joined', 'last_login', 'profile_completion'
        ]
    
    def get_profile_completion(self, obj):
        """Calculate profile completion percentage"""
        if obj.role == 'student' and hasattr(obj, 'student_profile'):
            return obj.student_profile.is_profile_complete
        elif obj.role == 'counselor' and hasattr(obj, 'counselor_profile'):
            profile = obj.counselor_profile
            total_fields = 8  # Important fields count
            completed_fields = sum([
                bool(profile.license_number),
                bool(profile.specializations),
                bool(profile.qualifications),
                bool(profile.experience_years),
                bool(profile.bio),
                bool(profile.languages_spoken),
                bool(profile.consultation_fee),
                bool(profile.session_duration_minutes)
            ])
            return (completed_fields / total_fields) * 100
        return 50  # Default for basic info completion