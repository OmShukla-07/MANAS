from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta, time, date
import json

from .models import (
    Appointment, AppointmentType, CounselorAvailability, 
    AppointmentNote, CounselorUnavailability
)
from accounts.models import CustomUser


@login_required
def appointments_list(request):
    """List all appointments for the current user"""
    if request.user.role == 'student':
        appointments = Appointment.objects.filter(student=request.user)
    elif request.user.role == 'counselor':
        appointments = Appointment.objects.filter(counselor=request.user)
    else:
        appointments = Appointment.objects.all()
    
    upcoming_appointments = appointments.filter(
        status__in=['pending', 'confirmed'],
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date', 'scheduled_time')
    
    past_appointments = appointments.filter(
        Q(status__in=['completed', 'cancelled_student', 'cancelled_counselor', 'no_show']) |
        Q(scheduled_date__lt=timezone.now().date())
    ).order_by('-scheduled_date', '-scheduled_time')
    
    context = {
        'upcoming_appointments': upcoming_appointments[:5],
        'past_appointments': past_appointments[:10],
        'user_role': request.user.role
    }
    return render(request, 'student/appointments.html', context)


@login_required
def book_appointment(request):
    """Book a new appointment"""
    if request.method == 'POST':
        try:
            # Get form data
            counselor_id = request.POST.get('counselor_id')
            appointment_type_id = request.POST.get('appointment_type_id')
            scheduled_date = request.POST.get('scheduled_date')
            scheduled_time = request.POST.get('scheduled_time')
            meeting_type = request.POST.get('meeting_type', 'video_call')
            reason = request.POST.get('reason', '')
            student_notes = request.POST.get('student_notes', '')
            
            # Validate required fields
            if not all([counselor_id, appointment_type_id, scheduled_date, scheduled_time]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('appointments_list')
            
            # Get objects
            counselor = get_object_or_404(CustomUser, id=counselor_id, role='counselor')
            appointment_type = get_object_or_404(AppointmentType, id=appointment_type_id)
            
            # Parse date and time
            scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
            scheduled_time = datetime.strptime(scheduled_time, '%H:%M').time()
            
            # Check if time slot is available
            existing_appointment = Appointment.objects.filter(
                counselor=counselor,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if existing_appointment:
                messages.error(request, 'This time slot is already booked.')
                return redirect('appointments_list')
            
            # Create appointment
            appointment = Appointment.objects.create(
                student=request.user,
                counselor=counselor,
                appointment_type=appointment_type,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                duration_minutes=appointment_type.duration_minutes,
                meeting_type=meeting_type,
                reason=reason,
                student_notes=student_notes,
                cost=appointment_type.price
            )
            
            messages.success(request, 'Appointment booked successfully!')
            return redirect('appointments_list')
            
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
            return redirect('appointments_list')
    
    # GET request - show booking form
    counselors = CustomUser.objects.filter(role='counselor', is_active=True)
    appointment_types = AppointmentType.objects.filter(is_active=True)
    
    context = {
        'counselors': counselors,
        'appointment_types': appointment_types,
        'meeting_types': Appointment.MeetingType.choices
    }
    return render(request, 'student/book_appointment.html', context)


@login_required
@require_http_methods(["GET"])
def get_available_slots(request):
    """AJAX endpoint to get available time slots for a counselor on a date"""
    counselor_id = request.GET.get('counselor_id')
    date_str = request.GET.get('date')
    
    if not counselor_id or not date_str:
        return JsonResponse({'error': 'Missing counselor_id or date'}, status=400)
    
    try:
        counselor = get_object_or_404(CustomUser, id=counselor_id, role='counselor')
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get counselor's availability for this day of week
        day_of_week = target_date.isoweekday()
        availability = CounselorAvailability.objects.filter(
            counselor=counselor,
            day_of_week=day_of_week,
            is_active=True
        ).first()
        
        if not availability:
            return JsonResponse({'slots': []})
        
        # Get existing appointments for this date
        existing_appointments = Appointment.objects.filter(
            counselor=counselor,
            scheduled_date=target_date,
            status__in=['pending', 'confirmed']
        ).values_list('scheduled_time', flat=True)
        
        # Generate available time slots
        available_slots = []
        current_time = availability.start_time
        end_time = availability.end_time
        slot_duration = timedelta(minutes=60)  # Default 1-hour slots
        
        while current_time < end_time:
            if current_time not in existing_appointments:
                available_slots.append({
                    'time': current_time.strftime('%H:%M'),
                    'display': current_time.strftime('%I:%M %p')
                })
            
            # Add slot duration
            current_datetime = datetime.combine(target_date, current_time)
            next_datetime = current_datetime + slot_duration
            current_time = next_datetime.time()
        
        return JsonResponse({'slots': available_slots})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if request.user.role == 'student' and appointment.student != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Check if cancellation is allowed
        if not appointment.can_cancel():
            return JsonResponse({
                'error': f'Cancellation not allowed within {appointment.appointment_type.cancellation_hours} hours'
            }, status=400)
        
        # Update status based on who is canceling
        if request.user.role == 'student':
            appointment.status = 'cancelled_student'
        else:
            appointment.status = 'cancelled_counselor'
        
        appointment.save()
        
        return JsonResponse({'success': True, 'message': 'Appointment cancelled successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def reschedule_appointment(request, appointment_id):
    """Reschedule an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if request.user.role == 'student' and appointment.student != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_time = datetime.strptime(data['time'], '%H:%M').time()
        
        # Check if new time slot is available
        existing_appointment = Appointment.objects.filter(
            counselor=appointment.counselor,
            scheduled_date=new_date,
            scheduled_time=new_time,
            status__in=['pending', 'confirmed']
        ).exclude(id=appointment_id).exists()
        
        if existing_appointment:
            return JsonResponse({'error': 'New time slot is already booked'}, status=400)
        
        # Update appointment
        appointment.scheduled_date = new_date
        appointment.scheduled_time = new_time
        appointment.status = 'pending'  # Needs re-confirmation
        appointment.save()
        
        return JsonResponse({'success': True, 'message': 'Appointment rescheduled successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def appointment_detail(request, appointment_id):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if request.user.role == 'student' and appointment.student != request.user:
        messages.error(request, 'Permission denied')
        return redirect('appointments_list')
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        messages.error(request, 'Permission denied')
        return redirect('appointments_list')
    
    notes = AppointmentNote.objects.filter(appointment=appointment)
    if request.user.role == 'student':
        notes = notes.filter(visible_to_student=True)
    
    context = {
        'appointment': appointment,
        'notes': notes,
        'can_cancel': appointment.can_cancel(),
        'is_upcoming': appointment.is_upcoming()
    }
    return render(request, 'student/appointment_detail.html', context)


@login_required
@require_http_methods(["GET"])
def counselor_schedule(request, counselor_id):
    """Get counselor's schedule for the calendar view"""
    counselor = get_object_or_404(CustomUser, id=counselor_id, role='counselor')
    
    # Get date range from query params
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # Default to current week
        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    
    # Get availability
    availability = CounselorAvailability.objects.filter(
        counselor=counselor,
        is_active=True
    )
    
    # Get appointments
    appointments = Appointment.objects.filter(
        counselor=counselor,
        scheduled_date__range=[start_date, end_date],
        status__in=['pending', 'confirmed']
    )
    
    # Build schedule data
    schedule_data = []
    
    # Add availability slots
    for avail in availability:
        schedule_data.append({
            'type': 'availability',
            'day_of_week': avail.day_of_week,
            'start_time': avail.start_time.strftime('%H:%M'),
            'end_time': avail.end_time.strftime('%H:%M')
        })
    
    # Add booked appointments
    for appointment in appointments:
        schedule_data.append({
            'type': 'appointment',
            'date': appointment.scheduled_date.strftime('%Y-%m-%d'),
            'time': appointment.scheduled_time.strftime('%H:%M'),
            'duration': appointment.duration_minutes,
            'student_name': appointment.student.get_full_name(),
            'appointment_type': appointment.appointment_type.name,
            'status': appointment.status
        })
    
    return JsonResponse({'schedule': schedule_data})


@login_required
@require_http_methods(["GET"])
def appointment_dashboard_stats(request):
    """Get appointment statistics for dashboard"""
    if request.user.role == 'student':
        appointments = Appointment.objects.filter(student=request.user)
    elif request.user.role == 'counselor':
        appointments = Appointment.objects.filter(counselor=request.user)
    else:
        appointments = Appointment.objects.all()
    
    today = timezone.now().date()
    
    stats = {
        'upcoming_count': appointments.filter(
            status__in=['pending', 'confirmed'],
            scheduled_date__gte=today
        ).count(),
        'completed_count': appointments.filter(status='completed').count(),
        'pending_count': appointments.filter(status='pending').count(),
        'this_week_count': appointments.filter(
            scheduled_date__week=today.isocalendar()[1],
            scheduled_date__year=today.year
        ).count(),
        'total_count': appointments.count()
    }
    
    # Recent appointments
    recent_appointments = appointments.filter(
        status__in=['completed', 'confirmed', 'pending']
    ).order_by('-scheduled_date', '-scheduled_time')[:5]
    
    recent_data = []
    for apt in recent_appointments:
        recent_data.append({
            'id': str(apt.id),
            'date': apt.scheduled_date.strftime('%Y-%m-%d'),
            'time': apt.scheduled_time.strftime('%H:%M'),
            'counselor_name': apt.counselor.get_full_name() if request.user.role == 'student' else apt.student.get_full_name(),
            'appointment_type': apt.appointment_type.name,
            'status': apt.get_status_display()
        })
    
    return JsonResponse({
        'stats': stats,
        'recent_appointments': recent_data
    })
