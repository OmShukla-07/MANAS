"""
Django management command to setup and migrate to Supabase database
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from core.supabase_service import supabase_service
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Command(BaseCommand):
    help = 'Setup and migrate MANAS database to Supabase PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check Supabase connection without migrating',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if Supabase connection test fails',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 MANAS Supabase Setup & Migration'))
        self.stdout.write('=' * 50)
        
        # Check Supabase configuration
        if not supabase_service.is_available():
            self.stdout.write(
                self.style.ERROR('❌ Supabase not configured!')
            )
            self.stdout.write(
                self.style.WARNING('Please set the following environment variables:')
            )
            self.stdout.write('  - SUPABASE_URL')
            self.stdout.write('  - SUPABASE_KEY')
            self.stdout.write('  - SUPABASE_SERVICE_ROLE_KEY (optional)')
            self.stdout.write('  - DATABASE_URL (PostgreSQL connection string)')
            return
        
        # Test Supabase connection
        self.stdout.write('🔍 Testing Supabase connection...')
        connection_test = supabase_service.test_connection()
        
        if connection_test['status'] == 'connected':
            self.stdout.write(
                self.style.SUCCESS(f'✅ {connection_test["message"]}')
            )
            self.stdout.write(f'   Database URL: {connection_test["database_url"]}')
            if 'users_count' in connection_test:
                self.stdout.write(f'   Users in database: {connection_test["users_count"]}')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {connection_test["message"]}')
            )
            if not options['force']:
                self.stdout.write(
                    self.style.WARNING('Use --force to proceed anyway')
                )
                return
        
        if options['check_only']:
            self.stdout.write(
                self.style.SUCCESS('✅ Supabase connection check complete!')
            )
            return
        
        # Check current database configuration
        db_config = settings.DATABASES['default']
        if 'sqlite' in db_config['ENGINE']:
            self.stdout.write(
                self.style.WARNING('⚠️ Currently using SQLite database')
            )
            self.stdout.write('Please update DATABASE_URL to use PostgreSQL for Supabase')
            self.stdout.write('Example: postgresql://postgres:[password]@[host]:[port]/[database]')
            return
        
        self.stdout.write(
            self.style.SUCCESS('✅ PostgreSQL database configured')
        )
        
        # Run Django migrations
        self.stdout.write('🗄️ Running Django migrations...')
        try:
            call_command('makemigrations', verbosity=0)
            call_command('migrate', verbosity=1)
            self.stdout.write(
                self.style.SUCCESS('✅ Django migrations completed successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration failed: {str(e)}')
            )
            return
        
        # Create superuser if needed
        self.stdout.write('👤 Checking for superuser...')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('⚠️ No superuser found. Creating one...')
            )
            try:
                call_command('createsuperuser', interactive=True)
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.WARNING('Superuser creation cancelled')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Superuser already exists')
            )
        
        # Test AI system
        self.stdout.write('🧠 Testing AI system...')
        try:
            from chat.enhanced_ai_service import enhanced_manas_ai_service
            providers = enhanced_manas_ai_service.get_available_providers()
            if providers:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ AI system ready with {len(providers)} providers')
                )
                for provider in providers:
                    self.stdout.write(f'   - {provider["name"]}: {provider["model"]}')
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ No AI providers available')
                )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ AI system check failed: {str(e)}')
            )
        
        # Final success message
        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write(
            self.style.SUCCESS('🎉 MANAS Supabase Setup Complete!')
        )
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Start the development server: python manage.py runserver')
        self.stdout.write('2. Access the admin panel: http://127.0.0.1:8000/admin/')
        self.stdout.write('3. Test the AI companions: http://127.0.0.1:8000/student/manas-ai/')
        self.stdout.write('4. Deploy to production with your Supabase database!')
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('🚀 MANAS is ready with Supabase!')
        )