from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import CustomUser, StudentProfile, CounselorProfile, AdminProfile


class Command(BaseCommand):
    help = 'Clean up user profiles and fix any database inconsistencies'

    def handle(self, *args, **options):
        self.stdout.write('Starting user profile cleanup...')
        
        with transaction.atomic():
            # Get all users
            users = CustomUser.objects.all()
            
            fixed_count = 0
            created_count = 0
            
            for user in users:
                try:
                    if user.role == 'student':
                        # Check if student profile exists
                        if not hasattr(user, 'student_profile'):
                            StudentProfile.objects.create(user=user)
                            created_count += 1
                            self.stdout.write(f'Created student profile for {user.email}')
                    
                    elif user.role == 'counselor':
                        # Check if counselor profile exists
                        if not hasattr(user, 'counselor_profile'):
                            CounselorProfile.objects.create(
                                user=user,
                                license_number=f"TEMP_{user.id}_{user.email.split('@')[0]}"
                            )
                            created_count += 1
                            self.stdout.write(f'Created counselor profile for {user.email}')
                    
                    elif user.role == 'admin':
                        # Check if admin profile exists
                        if not hasattr(user, 'admin_profile'):
                            AdminProfile.objects.create(user=user)
                            created_count += 1
                            self.stdout.write(f'Created admin profile for {user.email}')
                    
                    fixed_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error fixing profile for {user.email}: {e}')
                    )
            
            # Remove any orphaned profiles
            orphaned_students = StudentProfile.objects.filter(user__isnull=True)
            orphaned_counselors = CounselorProfile.objects.filter(user__isnull=True)
            orphaned_admins = AdminProfile.objects.filter(user__isnull=True)
            
            orphaned_count = (
                orphaned_students.count() + 
                orphaned_counselors.count() + 
                orphaned_admins.count()
            )
            
            if orphaned_count > 0:
                orphaned_students.delete()
                orphaned_counselors.delete()
                orphaned_admins.delete()
                self.stdout.write(f'Removed {orphaned_count} orphaned profiles')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Profile cleanup complete! '
                f'Processed {fixed_count} users, '
                f'created {created_count} missing profiles, '
                f'removed {orphaned_count} orphaned profiles.'
            )
        )