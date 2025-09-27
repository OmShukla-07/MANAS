from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from .models import (
    AppointmentType, Appointment, CounselorAvailability,
    CounselorUnavailability, AppointmentNote, AppointmentReminder,
    AppointmentTemplate
)

User = get_user_model()


class AppointmentTypeSerializer(serializers.ModelSerializer):
    """Serializer for appointment types"""
    
    class Meta:
        model = AppointmentType
        fields = '__all__'


class CounselorAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for counselor availability"""
    counselor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CounselorAvailability
        fields = [
            'id', 'counselor', 'counselor_name', 'day_of_week', 'specific_date',
            'start_time', 'end_time', 'max_appointments', 'current_appointments',
            'is_recurring', 'is_active', 'notes'
        ]
        read_only_fields = ['current_appointments']
    
    def get_counselor_name(self, obj):
        return obj.counselor.get_full_name()


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for appointment lists"""
    student_name = serializers.SerializerMethodField()
    counselor_name = serializers.SerializerMethodField()
    appointment_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'student', 'student_name', 'counselor', 'counselor_name',
            'appointment_type', 'appointment_type_name', 'scheduled_date',
            'scheduled_time', 'duration_minutes', 'status', 'emergency_session',
            'created_at'
        ]
    
    def get_student_name(self, obj):
        return obj.student.get_full_name()
    
    def get_counselor_name(self, obj):
        return obj.counselor.get_full_name()
    
    def get_appointment_type_name(self, obj):
        return obj.appointment_type.name if obj.appointment_type else None


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for appointments"""
    student_name = serializers.SerializerMethodField()
    counselor_name = serializers.SerializerMethodField()
    appointment_type_name = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_reschedule = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'student', 'student_name', 'counselor', 'counselor_name',
            'appointment_type', 'appointment_type_name', 'scheduled_date',
            'scheduled_time', 'duration_minutes', 'status', 'emergency_session',
            'reason', 'notes', 'preparation_instructions', 'follow_up_notes',
            'rating', 'feedback', 'cancellation_reason', 'rescheduled_from',
            'can_cancel', 'can_reschedule', 'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        return obj.student.get_full_name()
    
    def get_counselor_name(self, obj):
        return obj.counselor.get_full_name()
    
    def get_appointment_type_name(self, obj):
        return obj.appointment_type.name if obj.appointment_type else None
    
    def get_can_cancel(self, obj):
        if obj.status in ['cancelled', 'completed']:
            return False
        # Can cancel up to 2 hours before appointment
        appointment_datetime = timezone.datetime.combine(obj.scheduled_date, obj.scheduled_time)
        appointment_datetime = timezone.make_aware(appointment_datetime)
        return appointment_datetime > timezone.now() + timezone.timedelta(hours=2)
    
    def get_can_reschedule(self, obj):
        if obj.status in ['cancelled', 'completed']:
            return False
        # Can reschedule up to 4 hours before appointment
        appointment_datetime = timezone.datetime.combine(obj.scheduled_date, obj.scheduled_time)
        appointment_datetime = timezone.make_aware(appointment_datetime)
        return appointment_datetime > timezone.now() + timezone.timedelta(hours=4)


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating appointments"""
    
    class Meta:
        model = Appointment
        fields = [
            'counselor', 'appointment_type', 'scheduled_date', 'scheduled_time',
            'duration_minutes', 'reason', 'emergency_session'
        ]
    
    def validate(self, attrs):
        counselor = attrs['counselor']
        scheduled_date = attrs['scheduled_date']
        scheduled_time = attrs['scheduled_time']
        duration_minutes = attrs.get('duration_minutes', 60)
        
        # Check if counselor is available
        availability = CounselorAvailability.objects.filter(
            counselor=counselor,
            is_active=True
        ).filter(
            models.Q(specific_date=scheduled_date) |
            models.Q(day_of_week=scheduled_date.weekday(), is_recurring=True)
        ).filter(
            start_time__lte=scheduled_time,
            end_time__gte=scheduled_time
        ).first()
        
        if not availability:
            raise serializers.ValidationError("Counselor is not available at this time")
        
        # Check for conflicts
        end_time = (timezone.datetime.combine(scheduled_date, scheduled_time) + 
                   timezone.timedelta(minutes=duration_minutes)).time()
        
        conflicts = Appointment.objects.filter(
            counselor=counselor,
            scheduled_date=scheduled_date,
            status__in=['scheduled', 'confirmed'],
            scheduled_time__lt=end_time
        ).exclude(
            scheduled_time__gte=scheduled_time
        )
        
        if conflicts.exists():
            raise serializers.ValidationError("This time slot conflicts with another appointment")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentNoteSerializer(serializers.ModelSerializer):
    """Serializer for appointment notes"""
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AppointmentNote
        fields = [
            'id', 'appointment', 'author', 'author_name', 'note_type',
            'content', 'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def get_author_name(self, obj):
        return obj.author.get_full_name()


class AppointmentStatsSerializer(serializers.Serializer):
    """Serializer for appointment statistics"""
    total_appointments = serializers.IntegerField()
    upcoming_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    cancelled_appointments = serializers.IntegerField()
    emergency_appointments = serializers.IntegerField()
    average_rating = serializers.FloatField()
    total_counselors = serializers.IntegerField()
    available_counselors = serializers.IntegerField()


class CounselorScheduleSerializer(serializers.Serializer):
    """Serializer for counselor schedule"""
    date = serializers.DateField()
    available_slots = serializers.ListField(child=serializers.TimeField())
    booked_slots = serializers.ListField(child=serializers.TimeField())
    unavailable_periods = serializers.ListField(child=serializers.DictField())