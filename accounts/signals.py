from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import StudentProfile, CounselorProfile, AdminProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create appropriate profile when a user is created
    """
    if created:
        try:
            if instance.role == User.UserRole.STUDENT:
                # Check if profile already exists to avoid duplicate creation
                if not hasattr(instance, 'student_profile'):
                    StudentProfile.objects.create(user=instance)
            elif instance.role == User.UserRole.COUNSELOR:
                if not hasattr(instance, 'counselor_profile'):
                    CounselorProfile.objects.create(
                        user=instance,
                        license_number=f"TEMP_{instance.id}_{instance.email.split('@')[0]}"
                    )
            elif instance.role == User.UserRole.ADMIN:
                if not hasattr(instance, 'admin_profile'):
                    AdminProfile.objects.create(user=instance)
        except Exception as e:
            # Log the error but don't break user creation
            print(f"Error creating profile for user {instance.email}: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the user profile when the user is saved
    """
    try:
        if instance.role == User.UserRole.STUDENT and hasattr(instance, 'student_profile'):
            instance.student_profile.save()
        elif instance.role == User.UserRole.COUNSELOR and hasattr(instance, 'counselor_profile'):
            instance.counselor_profile.save()
        elif instance.role == User.UserRole.ADMIN and hasattr(instance, 'admin_profile'):
            instance.admin_profile.save()
    except Exception:
        # Profile doesn't exist yet, will be created by create_user_profile signal
        pass